# Cell-Based Architecture: Complete Code Samples

Complete executable code samples demonstrating cell-based architecture patterns for limiting blast radius at scale.

## Overview

This repository contains TypeScript/Node.js implementations of key cell-based architecture patterns:

- **Cell Router**: Maps tenant IDs to cell IDs with caching and refresh
- **Cell-Aware Middleware**: Express middleware that routes requests to the correct cell
- **Control Plane API**: Manages cells, tenants, and routing rules
- **API Server**: Example API server that uses cell-aware routing
- **Kubernetes Manifests**: Production-ready K8s configs for deploying cells

## Architecture

```
┌─────────────────┐
│  Control Plane  │
│   (Port 3001)   │
└────────┬────────┘
         │
         │ Routing API
         │
┌────────▼────────┐
│   API Gateway   │
│   (Port 3000)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │        │
┌───▼───┐ ┌──▼───┐
│Cell A │ │Cell B│
└───────┘ └──────┘
```

## Installation

```bash
npm install
```

## Build

```bash
npm run build
```

## Running the Examples

### 1. Start the Control Plane

The control plane manages cells, tenants, and routing rules:

```bash
npm run dev src/control-plane.ts
```

The control plane will start on port 3001 and provide:
- Health check: `http://localhost:3001/health`
- Routing API: `http://localhost:3001/api/routing/tenants`
- Cell API: `http://localhost:3001/api/cells`
- Tenant API: `http://localhost:3001/api/tenants`

### 2. Start the API Server

In a separate terminal, start the API server:

```bash
npm run dev src/api-server.ts
```

The API server will:
- Connect to the control plane
- Cache routing decisions
- Route requests to the correct cell based on tenant ID

### 3. Test Routing

Test the routing functionality:

```bash
npm run dev examples/routing-example.ts
```

This will:
- Connect to the control plane
- Look up cells for different tenants
- Display the routing mappings

### 4. Test API Requests

Make requests to the API server with different tenant IDs:

```bash
npm run dev examples/api-example.ts
```

Or use curl:

```bash
# Request with tenant ID
curl -H "X-Tenant-ID: tenant-acme" http://localhost:3000/api/users

# Create an order
curl -X POST -H "X-Tenant-ID: tenant-acme" \
  -H "Content-Type: application/json" \
  http://localhost:3000/api/orders
```

## Code Structure

```
src/
  ├── types.ts              # TypeScript interfaces for cells, tenants, routing
  ├── router.ts             # Cell router implementation
  ├── middleware.ts         # Express middleware for cell-aware routing
  ├── control-plane.ts      # Control plane API server
  ├── api-server.ts         # Example API server using cell routing
  └── index.ts              # Main entry point

examples/
  ├── routing-example.ts    # Example of using the router
  └── api-example.ts        # Example API requests

k8s/
  ├── cell-a-deployment.yaml    # Kubernetes deployment for a cell
  └── control-plane.yaml        # Kubernetes deployment for control plane

config/
  └── cell-schema.yaml      # YAML schema examples
```

## Key Components

### Cell Router

The `InMemoryCellRouter` caches tenant-to-cell mappings and refreshes them periodically from the control plane:

```typescript
const router = new InMemoryCellRouter('http://localhost:3001');
const cellId = await router.getCellForTenant('tenant-acme');
```

### Cell-Aware Middleware

Express middleware that extracts tenant ID and routes to the correct cell:

```typescript
app.use(cellAwareMiddleware(router));

app.get('/api/users', (req, res) => {
  const { cellContext } = req;
  // cellContext contains: tenantId, cellId, region
});
```

### Control Plane API

REST API for managing cells, tenants, and routing:

```bash
# Get routing table
curl http://localhost:3001/api/routing/tenants

# Get cell info
curl http://localhost:3001/api/cells/cell-us-east-1

# Create tenant
curl -X POST http://localhost:3001/api/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "id": "tenant-new",
    "cellId": "cell-us-east-1",
    "name": "New Tenant",
    "tier": "paid"
  }'

# Migrate tenant to different cell
curl -X POST http://localhost:3001/api/tenants/tenant-acme/migrate \
  -H "Content-Type: application/json" \
  -d '{"cellId": "cell-eu-west-1"}'
```

## Kubernetes Deployment

Deploy cells using the provided Kubernetes manifests:

```bash
# Create namespaces
kubectl create namespace cell-a
kubectl create namespace control-plane

# Deploy control plane
kubectl apply -f k8s/control-plane.yaml

# Deploy cell A
kubectl apply -f k8s/cell-a-deployment.yaml
```

## Key Patterns

### 1. Tenant-to-Cell Routing

- Extract tenant ID from request (JWT token or header)
- Look up cell ID from control plane
- Cache routing decisions for performance
- Refresh cache periodically

### 2. Cell Isolation

- Each cell has its own database, queue, and cache
- No cross-cell queries
- No synchronous RPC between cells
- Use events for rare cross-cell coordination

### 3. Control Plane

- Manages cell lifecycle
- Stores tenant-to-cell mappings
- Provides routing API
- Handles tenant migration

### 4. Observability

- Tag all logs, metrics, and traces with cell ID
- Monitor per-cell SLOs
- Alert per cell
- Compare cells to find anomalies

## Best Practices

1. **Start small**: Don't start with your largest tenant. Pick a low-risk group.
2. **Design for migration**: Moving tenants between cells should be easy.
3. **Monitor per cell**: You need observability to see what's happening in each cell.
4. **Cache routing decisions**: Don't hit the control plane for every request.
5. **Have rollback plan**: Things will go wrong. Be ready to rollback.
6. **Test routing logic**: Routing is critical. Test it thoroughly.

## Testing

Run the examples to see cell routing in action:

```bash
# Terminal 1: Start control plane
npm run dev src/control-plane.ts

# Terminal 2: Start API server
npm run dev src/api-server.ts

# Terminal 3: Test routing
npm run dev examples/routing-example.ts

# Terminal 4: Test API
npm run dev examples/api-example.ts
```

## Production Considerations

- **High availability**: Run control plane with multiple replicas
- **Database**: Use a real database for control plane (not in-memory)
- **Caching**: Use Redis or similar for distributed routing cache
- **Monitoring**: Add comprehensive metrics and alerting
- **Security**: Add authentication and authorization
- **Rate limiting**: Protect control plane from overload

## License

MIT
