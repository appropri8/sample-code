#!/bin/bash

# Verify mTLS is working for workloads in a namespace

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <namespace>"
    echo "Example: $0 my-app"
    exit 1
fi

NAMESPACE=$1

echo "Verifying mTLS for namespace: $NAMESPACE"
echo ""

# Check namespace is labeled
echo "1. Checking namespace label..."
LABEL=$(kubectl get namespace "$NAMESPACE" -o jsonpath='{.metadata.labels.istio\.io/dataplane-mode}' 2>/dev/null || echo "")
if [ "$LABEL" = "ambient" ]; then
    echo "✓ Namespace is labeled for ambient mode"
else
    echo "✗ Namespace is not labeled for ambient mode"
    echo "  Run: kubectl label namespace $NAMESPACE istio.io/dataplane-mode=ambient"
    exit 1
fi

echo ""

# Check pods have identity
echo "2. Checking pod identity..."
PODS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || echo "")
if [ -z "$PODS" ]; then
    echo "⚠ No pods found in namespace $NAMESPACE"
else
    echo "Pods in namespace:"
    kubectl get pods -n "$NAMESPACE" -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,IDENTITY:.metadata.labels.istio\.io/dataplane-mode
fi

echo ""

# Check ztunnel logs for TLS
echo "3. Checking ztunnel logs for TLS handshakes..."
ZTUNNEL_LOGS=$(kubectl logs -n istio-system -l app=ztunnel --tail=100 2>/dev/null | grep -i "$NAMESPACE" | grep -i tls | head -5 || echo "")
if [ -n "$ZTUNNEL_LOGS" ]; then
    echo "✓ Found TLS activity in ztunnel logs:"
    echo "$ZTUNNEL_LOGS"
else
    echo "⚠ No TLS activity found in ztunnel logs (may need to generate traffic)"
fi

echo ""

# Test connectivity if client pod exists
echo "4. Testing connectivity..."
CLIENT_POD=$(kubectl get pod -n "$NAMESPACE" -l app=echo-client -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$CLIENT_POD" ]; then
    echo "Found client pod: $CLIENT_POD"
    echo "Testing connection to echo-server..."
    if kubectl exec -n "$NAMESPACE" "$CLIENT_POD" -- curl -s -o /dev/null -w "%{http_code}" http://echo-server:8080 2>/dev/null | grep -q "200"; then
        echo "✓ Connection successful"
    else
        echo "⚠ Connection test failed (service may not be ready)"
    fi
else
    echo "⚠ No echo-client pod found (skipping connectivity test)"
fi

echo ""
echo "Verification complete!"
echo ""
echo "To view ztunnel logs:"
echo "  kubectl logs -n istio-system -l app=ztunnel --tail=100 | grep $NAMESPACE"

