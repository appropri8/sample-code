#!/bin/bash

# Example: Rollback a rate limit policy

CONTROL_PLANE_URL=${CONTROL_PLANE_URL:-"http://localhost:3000"}
POLICY_ID=${1:-"policy-123"}
TARGET_VERSION=${2:-"1"}

echo "Rolling back policy ${POLICY_ID} to version ${TARGET_VERSION}..."

curl -X POST "${CONTROL_PLANE_URL}/api/v1/rate-limit-policies/${POLICY_ID}/rollback" \
  -H "Content-Type: application/json" \
  -d "{
    \"targetVersion\": ${TARGET_VERSION},
    \"reason\": \"Rolling back due to issues\",
    \"userId\": \"admin-user\"
  }"

echo ""
echo "Policy rolled back!"
