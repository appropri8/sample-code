#!/bin/bash

# Example: Test a request through data plane

DATA_PLANE_URL=${DATA_PLANE_URL:-"http://localhost:3001"}

echo "Sending request to data plane..."

curl -X POST "${DATA_PLANE_URL}/api/request" \
  -H "Content-Type: application/json" \
  -d '{
    "tenantId": "tenant-123",
    "requestId": "req-$(date +%s)"
  }'

echo ""
echo "Request processed!"
