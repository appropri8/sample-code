package main

import (
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

// Counter tracks request counts
type Counter struct {
	value     int
	expiresAt time.Time
}

// CounterStore manages rate limit counters
type CounterStore interface {
	Increment(key string, ttl int) int
	Get(key string) int
}

// InMemoryCounterStore is an in-memory implementation
type InMemoryCounterStore struct {
	counters map[string]*Counter
	mu       sync.RWMutex
}

func NewInMemoryCounterStore() *InMemoryCounterStore {
	store := &InMemoryCounterStore{
		counters: make(map[string]*Counter),
	}
	// Cleanup expired counters
	go store.cleanup()
	return store
}

func (s *InMemoryCounterStore) Increment(key string, ttl int) int {
	s.mu.Lock()
	defer s.mu.Unlock()

	counter, exists := s.counters[key]
	if !exists || time.Now().After(counter.expiresAt) {
		counter = &Counter{
			value:     0,
			expiresAt: time.Now().Add(time.Duration(ttl) * time.Second),
		}
		s.counters[key] = counter
	}

	counter.value++
	return counter.value
}

func (s *InMemoryCounterStore) Get(key string) int {
	s.mu.RLock()
	defer s.mu.RUnlock()

	counter, exists := s.counters[key]
	if !exists || time.Now().After(counter.expiresAt) {
		return 0
	}
	return counter.value
}

func (s *InMemoryCounterStore) cleanup() {
	ticker := time.NewTicker(1 * time.Minute)
	for range ticker.C {
		s.mu.Lock()
		now := time.Now()
		for key, counter := range s.counters {
			if now.After(counter.expiresAt) {
				delete(s.counters, key)
			}
		}
		s.mu.Unlock()
	}
}

// RateLimiter checks if requests are allowed
type RateLimiter struct {
	policies      map[string]*RateLimitPolicy
	counters      CounterStore
	mu            sync.RWMutex
	defaultLimit  int
	defaultWindow int
}

func NewRateLimiter(counters CounterStore) *RateLimiter {
	return &RateLimiter{
		policies:      make(map[string]*RateLimitPolicy),
		counters:      counters,
		defaultLimit:  100, // Safe default
		defaultWindow: 60,  // 1 minute
	}
}

func (rl *RateLimiter) IsAllowed(tenantID string) bool {
	rl.mu.RLock()
	policy := rl.policies[tenantID]
	rl.mu.RUnlock()

	// Use default if no policy
	if policy == nil {
		policy = &RateLimitPolicy{
			Limit:  rl.defaultLimit,
			Window: rl.defaultWindow,
		}
	}

	// Create counter key based on time window
	windowStart := time.Now().Unix() / int64(policy.Window)
	key := fmt.Sprintf("%s:%d", tenantID, windowStart)

	count := rl.counters.Increment(key, policy.Window)
	return count <= policy.Limit
}

func (rl *RateLimiter) UpdatePolicy(policy *RateLimitPolicy) {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	existing := rl.policies[policy.TenantID]
	// Only update if version is newer
	if existing == nil || policy.Version > existing.Version {
		rl.policies[policy.TenantID] = policy
		log.Printf("Policy updated: tenant=%s, version=%d, limit=%d",
			policy.TenantID, policy.Version, policy.Limit)
	}
}

func (rl *RateLimiter) GetPolicy(tenantID string) *RateLimitPolicy {
	rl.mu.RLock()
	defer rl.mu.RUnlock()
	return rl.policies[tenantID]
}

// DataPlaneAPI handles data plane operations
type DataPlaneAPI struct {
	limiter         *RateLimiter
	controlPlaneURL string
}

func main() {
	counters := NewInMemoryCounterStore()
	limiter := NewRateLimiter(counters)

	controlPlaneURL := os.Getenv("CONTROL_PLANE_URL")
	if controlPlaneURL == "" {
		controlPlaneURL = "http://localhost:3000"
	}

	api := &DataPlaneAPI{
		limiter:         limiter,
		controlPlaneURL: controlPlaneURL,
	}

	// Start config watcher
	go api.startConfigWatcher()

	// Setup HTTP router
	r := mux.NewRouter()
	r.HandleFunc("/api/request", api.handleRequest).Methods("POST")
	r.HandleFunc("/internal/config/rate-limits", api.updateConfig).Methods("POST")
	r.HandleFunc("/health", api.health).Methods("GET")
	r.HandleFunc("/metrics", api.metrics).Methods("GET")

	port := os.Getenv("PORT")
	if port == "" {
		port = "3001"
	}

	log.Printf("Data plane running on port %s", port)
	log.Printf("Control plane URL: %s", controlPlaneURL)
	log.Fatal(http.ListenAndServe(":"+port, r))
}

func (api *DataPlaneAPI) handleRequest(w http.ResponseWriter, r *http.Request) {
	var req struct {
		TenantID  string `json:"tenantId"`
		RequestID string `json:"requestId"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Check rate limit
	if !api.limiter.IsAllowed(req.TenantID) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusTooManyRequests)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"error":    "rate limit exceeded",
			"tenantId": req.TenantID,
		})
		return
	}

	// Process request
	policy := api.limiter.GetPolicy(req.TenantID)
	response := map[string]interface{}{
		"status":    "allowed",
		"tenantId":  req.TenantID,
		"requestId": req.RequestID,
	}
	if policy != nil {
		response["limit"] = policy.Limit
		response["window"] = policy.Window
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (api *DataPlaneAPI) updateConfig(w http.ResponseWriter, r *http.Request) {
	var policy RateLimitPolicy
	if err := json.NewDecoder(r.Body).Decode(&policy); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	api.limiter.UpdatePolicy(&policy)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func (api *DataPlaneAPI) health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":   "healthy",
		"policies": len(api.limiter.policies),
	})
}

func (api *DataPlaneAPI) metrics(w http.ResponseWriter, r *http.Request) {
	api.limiter.mu.RLock()
	policyCount := len(api.limiter.policies)
	api.limiter.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"policies":        policyCount,
		"controlPlaneURL": api.controlPlaneURL,
	})
}

func (api *DataPlaneAPI) startConfigWatcher() {
	// Initial fetch
	api.fetchConfig()

	// Periodic refresh every 30 seconds
	ticker := time.NewTicker(30 * time.Second)
	for range ticker.C {
		api.fetchConfig()
	}
}

func (api *DataPlaneAPI) fetchConfig() {
	resp, err := http.Get(api.controlPlaneURL + "/api/v1/rate-limit-policies")
	if err != nil {
		log.Printf("Failed to fetch config from control plane: %v", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Control plane returned status %d", resp.StatusCode)
		return
	}

	var policies []RateLimitPolicy
	if err := json.NewDecoder(resp.Body).Decode(&policies); err != nil {
		log.Printf("Failed to decode policies: %v", err)
		return
	}

	// Update local cache
	for _, policy := range policies {
		api.limiter.UpdatePolicy(&policy)
	}
}
