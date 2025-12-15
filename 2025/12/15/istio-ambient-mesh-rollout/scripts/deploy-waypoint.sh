#!/bin/bash

# Deploy waypoint proxy for a namespace

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <namespace>"
    echo "Example: $0 my-app"
    exit 1
fi

NAMESPACE=$1

echo "Deploying waypoint proxy for namespace: $NAMESPACE"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "Error: Namespace $NAMESPACE does not exist"
    exit 1
fi

# Check if istioctl is available
if ! command -v istioctl &> /dev/null; then
    echo "Error: istioctl not found. Please install Istio first."
    exit 1
fi

# Deploy waypoint
istioctl x waypoint apply --namespace "$NAMESPACE"

echo "Waypoint proxy deployed for namespace: $NAMESPACE"
echo ""
echo "Verify:"
echo "  kubectl get pods -n $NAMESPACE -l istio.io/gateway-name=waypoint"
echo "  kubectl get svc -n $NAMESPACE -l istio.io/gateway-name=waypoint"

