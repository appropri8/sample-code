# From Ingress to Gateway API: Practical Examples

This repository contains executable code samples and examples for migrating from Kubernetes Ingress to Gateway API.

## Structure

```
.
├── gateways/          # Gateway and GatewayClass examples
├── httproutes/        # HTTPRoute examples (simple, canary, cross-namespace, etc.)
├── policies/          # ReferenceGrant and BackendTLSPolicy examples
├── examples/          # Complete end-to-end examples
├── migration/         # Ingress vs Gateway API comparison
├── scripts/            # Helper scripts for testing and migration
└── README.md          # This file
```

## Quick Start

### Prerequisites

- Kubernetes cluster (1.24+)
- Gateway API controller installed (Traefik, Envoy, NGINX, etc.)
- `kubectl` configured to access your cluster

### Install a Gateway API Controller

**Traefik (example):**

```bash
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik \
  --namespace traefik-system \
  --create-namespace \
  --set experimental.kubernetesGateway.enabled=true
```

**Verify GatewayClass:**

```bash
kubectl get gatewayclass
```

### Basic Example

1. Create a Gateway:

```bash
kubectl apply -f gateways/production-gateway.yaml
```

2. Create an HTTPRoute:

```bash
kubectl apply -f httproutes/simple-route.yaml
```

3. Check status:

```bash
kubectl get gateway production-gateway -n platform
kubectl get httproute frontend-route -n apps
```

4. Test routing:

```bash
# Get Gateway address
GATEWAY_IP=$(kubectl get gateway production-gateway -n platform -o jsonpath='{.status.addresses[0].value}')

# Test (replace with your hostname)
curl -H "Host: frontend.example.com" http://$GATEWAY_IP/
```

## Examples

### Simple Routing

- `httproutes/simple-route.yaml` - Basic routing to a single service

### Traffic Splitting (Canary)

- `httproutes/canary-route.yaml` - Split traffic 90/10 between versions
- `httproutes/blue-green-route.yaml` - Header-based blue-green deployment

### Advanced Patterns

- `httproutes/shadow-traffic-route.yaml` - Request mirroring for testing
- `httproutes/path-based-routing.yaml` - Multiple paths to different services
- `httproutes/cross-namespace-route.yaml` - Route to service in different namespace

### Cross-Namespace Routing

1. Create ReferenceGrant in target namespace:
```bash
kubectl apply -f policies/reference-grant-cross-namespace.yaml
```

2. Create HTTPRoute that references cross-namespace service:
```bash
kubectl apply -f httproutes/cross-namespace-route.yaml
```

### TLS and Certificates

- `examples/cert-manager-integration.yaml` - cert-manager with Gateway API
- Gateway TLS configuration in `gateways/production-gateway.yaml`

### WebSockets

- `examples/websocket-route.yaml` - WebSocket routing example

## Migration Guide

### Step 1: Inventory Existing Ingress

```bash
./scripts/migrate-ingress.sh
```

This creates a `migration-output/` directory with:
- List of all Ingress resources
- Exported YAML files
- Migration checklist

### Step 2: Map Patterns

Compare your Ingress resources with Gateway API equivalents:

- `migration/ingress-example.yaml` - Example Ingress
- `migration/gateway-api-equivalent.yaml` - Gateway API equivalent

### Step 3: Test Routing

```bash
./scripts/test-routing.sh platform production-gateway
```

## Common Patterns

### Central Gateway (Platform Team Owns)

```
platform namespace:
  - production-gateway (Gateway)

apps namespace:
  - frontend-route (HTTPRoute → production-gateway)
  - api-route (HTTPRoute → production-gateway)
```

### Per-Team Gateways

```
team-a namespace:
  - team-a-gateway (Gateway)
  - team-a-route (HTTPRoute → team-a-gateway)

team-b namespace:
  - team-b-gateway (Gateway)
  - team-b-route (HTTPRoute → team-b-gateway)
```

## Testing

### Check Gateway Status

```bash
kubectl get gateway production-gateway -n platform
kubectl describe gateway production-gateway -n platform
```

Look for:
- `Accepted: True`
- Listener status
- Address assignment

### Check HTTPRoute Status

```bash
kubectl get httproute --all-namespaces
kubectl describe httproute frontend-route -n apps
```

Look for:
- `Accepted: True`
- Parent status
- Backend status

### Test with curl

```bash
# Get Gateway address
GATEWAY_IP=$(kubectl get gateway production-gateway -n platform -o jsonpath='{.status.addresses[0].value}')

# Test HTTP
curl -H "Host: frontend.example.com" http://$GATEWAY_IP/

# Test HTTPS (if configured)
curl https://frontend.example.com/
```

## Troubleshooting

### Gateway not getting an address

1. Check controller is running:
```bash
kubectl get pods -n traefik-system
```

2. Check controller logs:
```bash
kubectl logs -n traefik-system -l app.kubernetes.io/name=traefik
```

3. Check GatewayClass:
```bash
kubectl get gatewayclass
kubectl describe gatewayclass traefik
```

### HTTPRoute not accepted

1. Check parent Gateway exists and is ready
2. Check namespace is allowed (Gateway `allowedRoutes`)
3. Check hostname conflicts
4. Check backend Service exists

### Cross-namespace routing not working

1. Verify ReferenceGrant exists in target namespace
2. Check ReferenceGrant `from` matches HTTPRoute namespace
3. Check ReferenceGrant `to` includes Service kind

## Resources

- [Gateway API Documentation](https://gateway-api.sigs.k8s.io/)
- [Gateway API Specification](https://gateway-api.sigs.k8s.io/reference/spec/)
- [Traefik Gateway API](https://doc.traefik.io/traefik/routing/providers/kubernetes-gateway/)
- [Envoy Gateway](https://gateway.envoyproxy.io/)
- [NGINX Gateway](https://github.com/nginxinc/nginx-gateway-fabric)

## License

This repository contains example code for educational purposes.
