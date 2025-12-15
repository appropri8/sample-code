# Istio Ambient Mesh Rollout

Complete examples and scripts for rolling out Istio ambient mode without sidecars. Get zero-trust L4 (mTLS) by default, add waypoint proxies only for workloads that need L7 features.

## Overview

This repository demonstrates how to:

- Install Istio with ambient mode enabled
- Enable ambient mode for namespaces (opt-in)
- Deploy waypoint proxies for L7 features
- Configure L4 and L7 policies
- Verify mTLS and traffic flow
- Roll back if needed

## Directory Structure

```
.
├── install/              # Installation manifests and scripts
│   ├── install-istio.sh
│   └── verify-install.sh
├── namespaces/          # Namespace examples with ambient labels
│   └── example-namespace.yaml
├── workloads/           # Example workloads (services, deployments)
│   ├── echo-server.yaml
│   └── echo-client.yaml
├── waypoints/           # Waypoint proxy deployments
│   └── namespace-waypoint.yaml
├── policies/            # AuthorizationPolicy examples
│   ├── l4-policy.yaml
│   └── l7-policy.yaml
├── examples/             # Complete end-to-end examples
│   └── complete-example.yaml
└── scripts/              # Setup and verification scripts
    ├── enable-ambient.sh
    ├── deploy-waypoint.sh
    ├── verify-mtls.sh
    └── rollback.sh
```

## Prerequisites

1. Kubernetes cluster (1.24+)
2. kubectl configured to access your cluster
3. istioctl installed (will be downloaded by install script)

## Quick Start

### 1. Install Istio with Ambient Mode

```bash
# Run installation script
chmod +x install/install-istio.sh
./install/install-istio.sh

# Verify installation
chmod +x install/verify-install.sh
./install/verify-install.sh
```

This installs:
- `istiod`: Control plane
- `ztunnel`: DaemonSet for L4 mTLS
- `istio-cni`: CNI plugin for traffic interception

### 2. Enable Ambient for a Namespace

```bash
# Enable ambient mode for a namespace
chmod +x scripts/enable-ambient.sh
./scripts/enable-ambient.sh my-app

# Or manually label the namespace
kubectl label namespace my-app istio.io/dataplane-mode=ambient
```

### 3. Deploy Example Workloads

```bash
# Create namespace
kubectl apply -f namespaces/example-namespace.yaml

# Deploy services
kubectl apply -f workloads/echo-server.yaml
kubectl apply -f workloads/echo-client.yaml
```

### 4. Verify mTLS is Working

```bash
# Test connectivity and verify mTLS
chmod +x scripts/verify-mtls.sh
./scripts/verify-mtls.sh my-app
```

### 5. Add Waypoint for L7 Features (Optional)

```bash
# Deploy waypoint for namespace
chmod +x scripts/deploy-waypoint.sh
./scripts/deploy-waypoint.sh my-app

# Or use istioctl
istioctl x waypoint apply --namespace my-app
```

## Examples

### Basic L4 Setup

Enable ambient mode and deploy workloads. Traffic is automatically encrypted with mTLS at L4.

```bash
# 1. Label namespace
kubectl label namespace my-app istio.io/dataplane-mode=ambient

# 2. Deploy workloads
kubectl apply -f workloads/echo-server.yaml -n my-app
kubectl apply -f workloads/echo-client.yaml -n my-app

# 3. Test connectivity
kubectl exec -n my-app <client-pod> -- curl http://echo-server:8080
```

### L4 Policy Example

Restrict access based on service account identity:

```bash
kubectl apply -f policies/l4-policy.yaml
```

This allows only the `frontend` service account to reach the `backend` service.

### L7 Policy Example

Add rate limiting or JWT validation (requires waypoint):

```bash
# 1. Deploy waypoint
istioctl x waypoint apply --namespace my-app

# 2. Apply L7 policy
kubectl apply -f policies/l7-policy.yaml
```

### Complete Example

See `examples/complete-example.yaml` for a full setup with:
- Namespace with ambient label
- Multiple services
- L4 authorization policy
- Waypoint proxy
- L7 authorization policy

## Verification Commands

### Check Installation

```bash
# Check istiod
kubectl get pods -n istio-system -l app=istiod

# Check ztunnel (one per node)
kubectl get pods -n istio-system -l app=ztunnel

# Check CNI
kubectl get pods -n istio-system -l app=istio-cni-node
```

### Check Namespace Opt-In

```bash
# Verify namespace is labeled
kubectl get namespace my-app -o jsonpath='{.metadata.labels.istio\.io/dataplane-mode}'
# Should output: ambient

# Check pods have identity
kubectl get pods -n my-app -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.labels.istio\.io/dataplane-mode}{"\n"}{end}'
```

### Check Waypoint

```bash
# Verify waypoint is running
kubectl get pods -n my-app -l istio.io/gateway-name=waypoint

# Check waypoint service
kubectl get svc -n my-app -l istio.io/gateway-name=waypoint
```

### Check Traffic Flow

```bash
# View ztunnel logs
kubectl logs -n istio-system -l app=ztunnel --tail=100 | grep -i tls

# View waypoint logs (if using L7)
kubectl logs -n my-app -l istio.io/gateway-name=waypoint --tail=100
```

## Rollback

To disable ambient mode for a namespace:

```bash
# Remove ambient label
kubectl label namespace my-app istio.io/dataplane-mode-

# Or use rollback script
chmod +x scripts/rollback.sh
./scripts/rollback.sh my-app
```

This immediately disables ambient mode. Pods continue running without restarts.

## Policy Examples

### L4 Authorization Policy

Allows only specific service accounts to communicate:

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: my-app
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/my-app/sa/frontend"]
```

### L7 Authorization Policy

Requires JWT token or applies rate limiting (needs waypoint):

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: require-jwt
  namespace: my-app
spec:
  selector:
    matchLabels:
      app: api
  action: ALLOW
  rules:
  - from:
    - source:
        requestPrincipals: ["*"]
    to:
    - operation:
        methods: ["GET", "POST"]
```

## Troubleshooting

### Pods Not Getting Identity

1. Check namespace is labeled: `kubectl get namespace <ns> -o yaml | grep dataplane-mode`
2. Check CNI is installed: `kubectl get pods -n istio-system -l app=istio-cni-node`
3. Check ztunnel logs: `kubectl logs -n istio-system -l app=ztunnel --tail=100`

### Traffic Not Encrypted

1. Verify ztunnel is intercepting: `kubectl logs -n istio-system -l app=ztunnel | grep <namespace>`
2. Check CNI configuration: `kubectl get configmap -n istio-system istio-cni-config -o yaml`
3. Verify pods have identity labels: `kubectl get pods -n <ns> --show-labels`

### Waypoint Not Working

1. Check waypoint pod is running: `kubectl get pods -n <ns> -l istio.io/gateway-name=waypoint`
2. Check waypoint service: `kubectl get svc -n <ns> -l istio.io/gateway-name=waypoint`
3. View waypoint logs: `kubectl logs -n <ns> -l istio.io/gateway-name=waypoint`

## Resources

- [Istio Ambient Mode Documentation](https://istio.io/latest/docs/ambient/)
- [Istio Installation Guide](https://istio.io/latest/docs/setup/install/)
- [AuthorizationPolicy Reference](https://istio.io/latest/docs/reference/config/security/authorization-policy/)

## License

This code is provided as-is for educational purposes.

