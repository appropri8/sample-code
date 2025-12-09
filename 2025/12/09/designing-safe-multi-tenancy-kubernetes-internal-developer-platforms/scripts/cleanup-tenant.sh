#!/bin/bash

# Script to cleanup a tenant namespace (USE WITH CAUTION)
# Usage: ./cleanup-tenant.sh <tenant-name>

set -e

TENANT_NAME="${1}"

if [ -z "$TENANT_NAME" ]; then
  echo "Usage: $0 <tenant-name>"
  echo "Example: $0 team-a"
  exit 1
fi

echo "⚠️  WARNING: This will delete namespace $TENANT_NAME and ALL resources in it!"
read -p "Are you sure? Type 'yes' to continue: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

echo "Deleting namespace: $TENANT_NAME"
kubectl delete namespace "$TENANT_NAME"

echo "✅ Namespace $TENANT_NAME deleted"
