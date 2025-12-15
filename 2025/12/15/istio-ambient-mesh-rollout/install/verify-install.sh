#!/bin/bash

# Verify Istio ambient mode installation

set -e

echo "Verifying Istio ambient mode installation..."
echo ""

# Check istiod
echo "Checking istiod..."
ISTIOD_PODS=$(kubectl get pods -n istio-system -l app=istiod --no-headers 2>/dev/null | wc -l)
if [ "$ISTIOD_PODS" -gt 0 ]; then
    echo "✓ istiod is running ($ISTIOD_PODS pod(s))"
    kubectl get pods -n istio-system -l app=istiod
else
    echo "✗ istiod is not running"
    exit 1
fi

echo ""

# Check ztunnel (should be one per node)
echo "Checking ztunnel..."
ZTUNNEL_PODS=$(kubectl get pods -n istio-system -l app=ztunnel --no-headers 2>/dev/null | wc -l)
if [ "$ZTUNNEL_PODS" -gt 0 ]; then
    echo "✓ ztunnel is running ($ZTUNNEL_PODS pod(s))"
    kubectl get pods -n istio-system -l app=ztunnel
else
    echo "✗ ztunnel is not running"
    exit 1
fi

echo ""

# Check CNI
echo "Checking istio-cni..."
CNI_PODS=$(kubectl get pods -n istio-system -l app=istio-cni-node --no-headers 2>/dev/null | wc -l)
if [ "$CNI_PODS" -gt 0 ]; then
    echo "✓ istio-cni is running ($CNI_PODS pod(s))"
    kubectl get pods -n istio-system -l app=istio-cni-node
else
    echo "⚠ istio-cni is not running (may be installed differently)"
fi

echo ""
echo "Installation verification complete!"

