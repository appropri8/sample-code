#!/bin/bash

# Example: Create a rate limit policy via control plane API

CONTROL_PLANE_URL=${CONTROL_PLANE_URL:-"http://localhost:3000"}

echo "Creating rate limit policy..."

curl -X POST "${CONTROL_PLANE_URL}/api/v1/rate-limit-policies" \
  -H "Content-Type: application/json" \
  -d '{
    "tenantId": "tenant-123",
    "limit": 1000,
    "window": 60,
    "userId": "admin-user"
  }'

echo ""
echo "Policy created!"
