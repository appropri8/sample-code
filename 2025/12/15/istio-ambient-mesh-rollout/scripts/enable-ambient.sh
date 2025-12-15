#!/bin/bash

# Enable ambient mode for a namespace

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <namespace>"
    echo "Example: $0 my-app"
    exit 1
fi

NAMESPACE=$1

echo "Enabling ambient mode for namespace: $NAMESPACE"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# Label namespace for ambient mode
kubectl label namespace "$NAMESPACE" istio.io/dataplane-mode=ambient --overwrite

echo "Ambient mode enabled for namespace: $NAMESPACE"
echo ""
echo "Verify:"
echo "  kubectl get namespace $NAMESPACE -o jsonpath='{.metadata.labels.istio\.io/dataplane-mode}'"
echo ""
echo "Pods in this namespace will automatically get ambient mode identity."

