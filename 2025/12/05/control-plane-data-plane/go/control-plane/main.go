package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gorilla/mux"
)

// RateLimitPolicy represents a rate limiting policy
type RateLimitPolicy struct {
	ID        string    `json:"id"`
	Version   int       `json:"version"`
	TenantID  string    `json:"tenantId"`
	Limit     int       `json:"limit"`
	Window    int       `json:"window"` // seconds
	CreatedAt time.Time `json:"createdAt"`
	UpdatedAt time.Time `json:"updatedAt"`
}

// ControlPlaneAPI handles control plane operations
type ControlPlaneAPI struct {
	policies      map[string]*RateLimitPolicy
	versions      map[string][]*RateLimitPolicy // version history
	dataPlaneURLs []string
	mu            sync.RWMutex
	auditLog      []AuditEntry
}

// AuditEntry logs all changes
type AuditEntry struct {
	Action     string    `json:"action"`
	ResourceID string    `json:"resourceId"`
	UserID     string    `json:"userId"`
	Changes    string    `json:"changes"`
	Timestamp  time.Time `json:"timestamp"`
}

func main() {
	api := &ControlPlaneAPI{
		policies:      make(map[string]*RateLimitPolicy),
		versions:      make(map[string][]*RateLimitPolicy),
		dataPlaneURLs: []string{"http://localhost:3001"},
		auditLog:      make([]AuditEntry, 0),
	}

	// Start reconciliation loop
	go api.startReconciliation()

	// Setup HTTP router
	r := mux.NewRouter()
	r.HandleFunc("/api/v1/rate-limit-policies", api.createPolicy).Methods("POST")
	r.HandleFunc("/api/v1/rate-limit-policies/{id}", api.getPolicy).Methods("GET")
	r.HandleFunc("/api/v1/rate-limit-policies/{id}", api.updatePolicy).Methods("PUT")
	r.HandleFunc("/api/v1/rate-limit-policies/{id}/rollback", api.rollbackPolicy).Methods("POST")
	r.HandleFunc("/api/v1/rate-limit-policies", api.listPolicies).Methods("GET")
	r.HandleFunc("/api/v1/audit", api.getAuditLog).Methods("GET")
	r.HandleFunc("/health", api.health).Methods("GET")

	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}

	log.Printf("Control plane running on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, r))
}

func (api *ControlPlaneAPI) createPolicy(w http.ResponseWriter, r *http.Request) {
	var req struct {
		TenantID string `json:"tenantId"`
		Limit    int    `json:"limit"`
		Window   int    `json:"window"`
		UserID   string `json:"userId"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Validate
	if req.Limit <= 0 || req.Window <= 0 {
		http.Error(w, "limit and window must be positive", http.StatusBadRequest)
		return
	}

	// Create policy
	policy := &RateLimitPolicy{
		ID:        generateID(),
		Version:   1,
		TenantID:  req.TenantID,
		Limit:     req.Limit,
		Window:    req.Window,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	api.mu.Lock()
	api.policies[policy.ID] = policy
	api.versions[policy.ID] = []*RateLimitPolicy{policy}
	api.mu.Unlock()

	// Audit log
	api.logAudit("CREATE_RATE_LIMIT_POLICY", policy.ID, req.UserID, fmt.Sprintf("limit=%d, window=%d", req.Limit, req.Window))

	// Push to data plane (async)
	go api.pushToDataPlane(policy)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(policy)
}

func (api *ControlPlaneAPI) getPolicy(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]
	version := r.URL.Query().Get("version")

	api.mu.RLock()
	defer api.mu.RUnlock()

	if version != "" {
		// Get specific version
		versions := api.versions[id]
		for _, v := range versions {
			if fmt.Sprintf("%d", v.Version) == version {
				json.NewEncoder(w).Encode(v)
				return
			}
		}
		http.Error(w, "version not found", http.StatusNotFound)
		return
	}

	// Get latest
	policy, exists := api.policies[id]
	if !exists {
		http.Error(w, "policy not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(policy)
}

func (api *ControlPlaneAPI) updatePolicy(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	var req struct {
		Limit  *int   `json:"limit"`
		Window *int   `json:"window"`
		UserID string `json:"userId"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	api.mu.Lock()
	policy, exists := api.policies[id]
	if !exists {
		api.mu.Unlock()
		http.Error(w, "policy not found", http.StatusNotFound)
		return
	}

	// Create new version
	newPolicy := *policy
	if req.Limit != nil {
		newPolicy.Limit = *req.Limit
	}
	if req.Window != nil {
		newPolicy.Window = *req.Window
	}
	newPolicy.Version = policy.Version + 1
	newPolicy.UpdatedAt = time.Now()

	api.policies[id] = &newPolicy
	api.versions[id] = append(api.versions[id], &newPolicy)
	api.mu.Unlock()

	// Audit log
	api.logAudit("UPDATE_RATE_LIMIT_POLICY", id, req.UserID, fmt.Sprintf("version=%d", newPolicy.Version))

	// Push to data plane (async)
	go api.pushToDataPlane(&newPolicy)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(&newPolicy)
}

func (api *ControlPlaneAPI) rollbackPolicy(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	var req struct {
		TargetVersion int    `json:"targetVersion"`
		Reason        string `json:"reason"`
		UserID        string `json:"userId"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	api.mu.Lock()
	versions := api.versions[id]
	var targetPolicy *RateLimitPolicy
	for _, v := range versions {
		if v.Version == req.TargetVersion {
			targetPolicy = v
			break
		}
	}
	api.mu.Unlock()

	if targetPolicy == nil {
		http.Error(w, "version not found", http.StatusNotFound)
		return
	}

	// Create new version pointing to old config
	rolledBack := *targetPolicy
	rolledBack.Version = api.policies[id].Version + 1
	rolledBack.UpdatedAt = time.Now()

	api.mu.Lock()
	api.policies[id] = &rolledBack
	api.versions[id] = append(api.versions[id], &rolledBack)
	api.mu.Unlock()

	// Audit log
	api.logAudit("ROLLBACK_RATE_LIMIT_POLICY", id, req.UserID, fmt.Sprintf("to version %d: %s", req.TargetVersion, req.Reason))

	// Push to data plane (async)
	go api.pushToDataPlane(&rolledBack)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(&rolledBack)
}

func (api *ControlPlaneAPI) listPolicies(w http.ResponseWriter, r *http.Request) {
	api.mu.RLock()
	policies := make([]*RateLimitPolicy, 0, len(api.policies))
	for _, p := range api.policies {
		policies = append(policies, p)
	}
	api.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(policies)
}

func (api *ControlPlaneAPI) getAuditLog(w http.ResponseWriter, r *http.Request) {
	api.mu.RLock()
	log := make([]AuditEntry, len(api.auditLog))
	copy(log, api.auditLog)
	api.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(log)
}

func (api *ControlPlaneAPI) health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":   "healthy",
		"policies": len(api.policies),
	})
}

func (api *ControlPlaneAPI) pushToDataPlane(policy *RateLimitPolicy) {
	for _, url := range api.dataPlaneURLs {
		body, _ := json.Marshal(policy)
		resp, err := http.Post(url+"/internal/config/rate-limits", "application/json", bytes.NewBuffer(body))
		if err != nil {
			log.Printf("Failed to push to data plane %s: %v", url, err)
			continue
		}
		resp.Body.Close()
	}
}

func (api *ControlPlaneAPI) startReconciliation() {
	ticker := time.NewTicker(30 * time.Second)
	for range ticker.C {
		api.reconcile()
	}
}

func (api *ControlPlaneAPI) reconcile() {
	api.mu.RLock()
	policies := make([]*RateLimitPolicy, 0, len(api.policies))
	for _, p := range api.policies {
		policies = append(policies, p)
	}
	api.mu.RUnlock()

	for _, policy := range policies {
		api.pushToDataPlane(policy)
	}
}

func (api *ControlPlaneAPI) logAudit(action, resourceID, userID, changes string) {
	api.mu.Lock()
	api.auditLog = append(api.auditLog, AuditEntry{
		Action:     action,
		ResourceID: resourceID,
		UserID:     userID,
		Changes:    changes,
		Timestamp:  time.Now(),
	})
	api.mu.Unlock()
}

func generateID() string {
	return fmt.Sprintf("policy-%d", time.Now().UnixNano())
}
