package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	"github.com/gorilla/mux"
)

func main() {
	controlPlaneURL := os.Getenv("CONTROL_PLANE_URL")
	if controlPlaneURL == "" {
		controlPlaneURL = "http://localhost:3001"
	}

	// Initialize router
	router := NewInMemoryCellRouter(controlPlaneURL)

	// Create HTTP router
	r := mux.NewRouter()

	// Apply cell-aware middleware
	r.Use(CellAwareMiddleware(router))

	// API endpoints
	r.HandleFunc("/api/users", handleGetUsers).Methods("GET")
	r.HandleFunc("/api/orders", handleCreateOrder).Methods("POST")
	r.HandleFunc("/health", handleHealth(router)).Methods("GET")
	r.HandleFunc("/metrics", handleMetrics(router, controlPlaneURL)).Methods("GET")

	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}

	fmt.Printf("API server running on port %s\n", port)
	fmt.Printf("Cell router connected to: %s\n", controlPlaneURL)

	if err := http.ListenAndServe(":"+port, r); err != nil {
		fmt.Printf("Server failed: %v\n", err)
		os.Exit(1)
	}
}

func handleGetUsers(w http.ResponseWriter, r *http.Request) {
	cellContext := GetCellContext(r)
	if cellContext == nil {
		http.Error(w, `{"error":"Cell context missing"}`, http.StatusInternalServerError)
		return
	}

	response := map[string]interface{}{
		"message":  "Users retrieved",
		"cellId":   cellContext.CellID,
		"tenantId": cellContext.TenantID,
		"region":   cellContext.Region,
		"users": []map[string]string{
			{"id": "1", "name": "User 1"},
			{"id": "2", "name": "User 2"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func handleCreateOrder(w http.ResponseWriter, r *http.Request) {
	cellContext := GetCellContext(r)
	if cellContext == nil {
		http.Error(w, `{"error":"Cell context missing"}`, http.StatusInternalServerError)
		return
	}

	response := map[string]interface{}{
		"message":  "Order created",
		"cellId":   cellContext.CellID,
		"tenantId": cellContext.TenantID,
		"orderId":  fmt.Sprintf("order-%d", r.Context().Value("timestamp")),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func handleHealth(router *InMemoryCellRouter) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		response := map[string]interface{}{
			"status":          "healthy",
			"routerCacheSize": router.GetCacheSize(),
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}
}

func handleMetrics(router *InMemoryCellRouter, controlPlaneURL string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		response := map[string]interface{}{
			"routerCacheSize": router.GetCacheSize(),
			"controlPlaneURL": controlPlaneURL,
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}
}
