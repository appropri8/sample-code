package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"
)

// TenantMapping represents a mapping from tenant ID to cell ID
type TenantMapping struct {
	TenantID string `json:"tenantId"`
	CellID   string `json:"cellId"`
}

// RoutingResponse is the response from the control plane routing API
type RoutingResponse struct {
	Mappings  []TenantMapping `json:"mappings"`
	Version   int             `json:"version"`
	UpdatedAt string          `json:"updatedAt"`
}

// CellRouter routes tenant IDs to cell IDs
type CellRouter interface {
	GetCellForTenant(tenantID string) (string, error)
	Refresh() error
	Stop()
}

// InMemoryCellRouter implements CellRouter with in-memory caching
type InMemoryCellRouter struct {
	controlPlaneURL string
	tenantToCell    map[string]string
	mu              sync.RWMutex
	refreshInterval time.Duration
	stopChan        chan struct{}
	httpClient      *http.Client
}

// NewInMemoryCellRouter creates a new router instance
func NewInMemoryCellRouter(controlPlaneURL string) *InMemoryCellRouter {
	router := &InMemoryCellRouter{
		controlPlaneURL: controlPlaneURL,
		tenantToCell:    make(map[string]string),
		refreshInterval: 5 * time.Minute,
		stopChan:        make(chan struct{}),
		httpClient:      &http.Client{Timeout: 10 * time.Second},
	}

	// Start background refresh
	go router.startRefresh()

	return router
}

// GetCellForTenant looks up the cell ID for a tenant
func (r *InMemoryCellRouter) GetCellForTenant(tenantID string) (string, error) {
	// Check cache first
	r.mu.RLock()
	cellID, found := r.tenantToCell[tenantID]
	r.mu.RUnlock()

	if found {
		return cellID, nil
	}

	// If not in cache, refresh and try again
	if err := r.Refresh(); err != nil {
		return "", fmt.Errorf("failed to refresh routing table: %w", err)
	}

	r.mu.RLock()
	cellID, found = r.tenantToCell[tenantID]
	r.mu.RUnlock()

	if !found {
		return "", fmt.Errorf("no cell found for tenant: %s", tenantID)
	}

	return cellID, nil
}

// Refresh fetches the latest routing table from the control plane
func (r *InMemoryCellRouter) Refresh() error {
	url := fmt.Sprintf("%s/api/routing/tenants", r.controlPlaneURL)

	resp, err := r.httpClient.Get(url)
	if err != nil {
		return fmt.Errorf("failed to fetch routing table: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("control plane returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response: %w", err)
	}

	var routingResp RoutingResponse
	if err := json.Unmarshal(body, &routingResp); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	// Update cache
	r.mu.Lock()
	r.tenantToCell = make(map[string]string)
	for _, mapping := range routingResp.Mappings {
		r.tenantToCell[mapping.TenantID] = mapping.CellID
	}
	r.mu.Unlock()

	fmt.Printf("Refreshed routing table: %d tenant mappings\n", len(routingResp.Mappings))
	return nil
}

// startRefresh runs periodic refresh in the background
func (r *InMemoryCellRouter) startRefresh() {
	// Initial refresh
	r.Refresh()

	ticker := time.NewTicker(r.refreshInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			r.Refresh()
		case <-r.stopChan:
			return
		}
	}
}

// Stop stops the background refresh
func (r *InMemoryCellRouter) Stop() {
	close(r.stopChan)
}

// GetCacheSize returns the number of cached mappings
func (r *InMemoryCellRouter) GetCacheSize() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.tenantToCell)
}
