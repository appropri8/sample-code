#!/bin/bash

# Rollback ambient mode for a namespace

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <namespace>"
    echo "Example: $0 my-app"
    exit 1
fi

NAMESPACE=$1

echo "Rolling back ambient mode for namespace: $NAMESPACE"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "Error: Namespace $NAMESPACE does not exist"
    exit 1
fi

# Remove ambient label
kubectl label namespace "$NAMESPACE" istio.io/dataplane-mode- 2>/dev/null || true

# Remove waypoint if exists
echo "Removing waypoint proxy (if exists)..."
kubectl delete deployment -n "$NAMESPACE" -l istio.io/gateway-name=waypoint 2>/dev/null || true
kubectl delete service -n "$NAMESPACE" -l istio.io/gateway-name=waypoint 2>/dev/null || true

echo "Ambient mode disabled for namespace: $NAMESPACE"
echo ""
echo "Note: Pods will continue running. No restarts required."
echo ""
echo "Verify:"
echo "  kubectl get namespace $NAMESPACE -o jsonpath='{.metadata.labels.istio\.io/dataplane-mode}'"
echo "  (should be empty)"

