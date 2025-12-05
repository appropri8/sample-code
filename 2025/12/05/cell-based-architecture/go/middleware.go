package main

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

// CellContext contains cell routing information
type CellContext struct {
	TenantID string
	CellID   string
	Region   string
}

type contextKey string

const cellContextKey contextKey = "cellContext"

// CellAwareMiddleware creates middleware that routes requests to the correct cell
func CellAwareMiddleware(router CellRouter) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract tenant ID
			tenantID := extractTenantID(r)
			if tenantID == "" {
				http.Error(w, `{"error":"Missing tenant ID"}`, http.StatusUnauthorized)
				return
			}

			// Look up cell ID
			cellID, err := router.GetCellForTenant(tenantID)
			if err != nil {
				http.Error(w, fmt.Sprintf(`{"error":"No cell available for tenant","tenantId":"%s"}`, tenantID), http.StatusServiceUnavailable)
				return
			}

			// Create cell context
			cellContext := CellContext{
				TenantID: tenantID,
				CellID:   cellID,
				Region:   extractRegion(r),
			}

			// Add to request context
			ctx := context.WithValue(r.Context(), cellContextKey, cellContext)
			r = r.WithContext(ctx)

			// Add headers for downstream services
			r.Header.Set("X-Cell-ID", cellID)
			r.Header.Set("X-Tenant-ID", tenantID)

			next.ServeHTTP(w, r)
		})
	}
}

// GetCellContext extracts cell context from request
func GetCellContext(r *http.Request) *CellContext {
	ctx := r.Context().Value(cellContextKey)
	if ctx == nil {
		return nil
	}
	cellCtx, ok := ctx.(CellContext)
	if !ok {
		return nil
	}
	return &cellCtx
}

func extractTenantID(r *http.Request) string {
	// Try JWT token first
	authHeader := r.Header.Get("Authorization")
	if strings.HasPrefix(authHeader, "Bearer ") {
		token := strings.TrimPrefix(authHeader, "Bearer ")
		if tenantID := parseJWT(token); tenantID != "" {
			return tenantID
		}
	}

	// Fallback to header
	return r.Header.Get("X-Tenant-ID")
}

func extractRegion(r *http.Request) string {
	if region := r.Header.Get("X-Region"); region != "" {
		return region
	}
	if region := r.Header.Get("Cf-Ipcountry"); region != "" {
		return region
	}
	return ""
}

func parseJWT(token string) string {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return ""
	}

	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return ""
	}

	var claims map[string]interface{}
	if err := json.Unmarshal(payload, &claims); err != nil {
		return ""
	}

	if tenantID, ok := claims["tenantId"].(string); ok {
		return tenantID
	}

	return ""
}
