#!/bin/bash

# Install Istio with ambient mode enabled
# This script downloads istioctl and installs Istio with the ambient profile

set -e

echo "Installing Istio with ambient mode..."

# Download Istio if not already present
ISTIO_VERSION="1.20.0"
ISTIO_DIR="istio-${ISTIO_VERSION}"

if [ ! -d "$ISTIO_DIR" ]; then
    echo "Downloading Istio ${ISTIO_VERSION}..."
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
fi

cd "$ISTIO_DIR"

# Add istioctl to PATH
export PATH=$PWD/bin:$PATH

# Install Istio with ambient profile
echo "Installing Istio with ambient profile..."
istioctl install --set profile=ambient --set values.defaultRevision=ambient -y

echo "Waiting for Istio components to be ready..."
kubectl wait --for=condition=ready pod -l app=istiod -n istio-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=ztunnel -n istio-system --timeout=300s

echo "Istio ambient mode installed successfully!"
echo ""
echo "Verify installation:"
echo "  kubectl get pods -n istio-system"
echo "  kubectl get pods -n istio-system -l app=ztunnel"
echo "  kubectl get pods -n istio-system -l app=istiod"

