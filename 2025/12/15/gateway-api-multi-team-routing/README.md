# Gateway API Multi-Team Routing

Complete examples and manifests for implementing Gateway API with clear ownership boundaries between platform teams and app teams.

## Overview

This repository demonstrates how to use Kubernetes Gateway API to replace Ingress sprawl with role-oriented routing:

- **Platform teams** own GatewayClass and Gateway resources (infrastructure)
- **App teams** own HTTPRoute resources (routing intent)
- Clear boundaries prevent teams from stepping on each other

## Directory Structure

```
.
├── gateways/              # GatewayClass and Gateway resources (platform team)
│   ├── gatewayclass-traefik.yaml
│   └── production-gateway.yaml
├── httproutes/           # HTTPRoute examples (app teams)
│   ├── simple-route.yaml
│   ├── path-based-routing.yaml
│   ├── canary-route.yaml
│   ├── shadow-traffic-route.yaml
│   ├── route-with-timeouts.yaml
│   └── protected-route.yaml
├── policies/             # ReferenceGrant and other policies
│   └── reference-grant-cross-namespace.yaml
├── examples/             # Complete end-to-end examples
│   └── complete-example.yaml
└── scripts/              # Setup and testing scripts
    ├── setup-gateway.sh
    └── test-routing.sh
```

## Prerequisites

1. Kubernetes cluster (1.24+)
2. Gateway API CRDs installed:
   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
   ```
3. Gateway API controller (e.g., Traefik, Envoy, NGINX)
   - For Traefik: `helm install traefik traefik/traefik --set gatewayAPI.enabled=true`

## Quick Start

### 1. Platform Team Setup

Create the shared gateway infrastructure:

```bash
# Create gateway-system namespace
kubectl create namespace gateway-system

# Label namespace to allow route attachment
kubectl label namespace gateway-system gateway-access=enabled

# Apply GatewayClass
kubectl apply -f gateways/gatewayclass-traefik.yaml

# Apply Gateway
kubectl apply -f gateways/production-gateway.yaml

# Or use the setup script
chmod +x scripts/setup-gateway.sh
./scripts/setup-gateway.sh
```

### 2. App Team Setup

Label your namespace to allow route attachment:

```bash
kubectl label namespace team-a gateway-access=enabled
```

Create HTTPRoutes in your namespace:

```bash
kubectl apply -f httproutes/simple-route.yaml
```

## Examples

### Basic Host + Path Routing

See `httproutes/simple-route.yaml` for a basic route that forwards all traffic to a service.

See `httproutes/path-based-routing.yaml` for path-based routing to multiple services.

### Weighted Backends (Canary Deployment)

See `httproutes/canary-route.yaml` for splitting traffic between two backends by weight (90/10 split).

### Request Mirroring (Shadow Traffic)

See `httproutes/shadow-traffic-route.yaml` for mirroring 10% of requests to a test backend.

### Retries and Timeouts

See `httproutes/route-with-timeouts.yaml` for configuring request timeouts and retry policies.

### External Authentication

See `httproutes/protected-route.yaml` for integrating OIDC authentication (Traefik-specific example).

## Ownership Model

### Platform Team Owns

- **GatewayClass**: Defines which controller implementation is available
- **Gateway**: Defines shared infrastructure (listeners, TLS, ports)
- **TLS Certificates**: Managed in `gateway-system` namespace
- **Gateway-level Policies**: Rate limiting, security policies

### App Teams Own

- **HTTPRoute**: Defines routing rules in their own namespaces
- **Backend Services**: Services that routes point to
- **Route-level Policies**: Request modifications, filters

### Guardrails

- **Allowed Namespaces**: Gateway restricts which namespaces can attach routes
- **Allowed Hostnames**: Teams can only use hostnames matching Gateway listener patterns
- **Route Attachment Policies**: Additional validation (implementation-specific)

## Testing

Run the test script to verify Gateway API routing:

```bash
chmod +x scripts/test-routing.sh
./scripts/test-routing.sh
```

## Migration from Ingress

1. **Phase 1**: Install Gateway API controller alongside existing Ingress controller
2. **Phase 2**: Create Gateway and migrate one domain/team
3. **Phase 3**: Gradually migrate remaining teams
4. **Phase 4**: Remove old Ingress resources

See the article for detailed migration steps.

## Implementation Notes

- **Controller-Specific Features**: Some features (like external auth) are implementation-specific. The `protected-route.yaml` example shows Traefik's approach.
- **TLS Certificates**: Use cert-manager in production instead of manually creating Secrets.
- **Cross-Namespace References**: Use ReferenceGrant to allow HTTPRoutes to reference Gateways in different namespaces.

## Resources

- [Gateway API Documentation](https://gateway-api.sigs.k8s.io/)
- [Gateway API Specification](https://gateway-api.sigs.k8s.io/reference/spec/)
- [Traefik Gateway API Support](https://doc.traefik.io/traefik/routing/providers/kubernetes-gateway/)

## License

This code is provided as-is for educational purposes.

