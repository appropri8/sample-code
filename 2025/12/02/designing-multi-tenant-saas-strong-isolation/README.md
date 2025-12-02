# Designing Multi-Tenant SaaS with Strong Isolation

Complete executable code samples demonstrating how to design multi-tenant SaaS systems with strong isolation by default. Tenants share the platform but don't share failure modes, noisy neighbors, or data.

## Overview

This repository contains TypeScript/Node.js implementations of key multi-tenant isolation patterns:

- **Tenant Context Propagation**: Extract tenant ID from requests and flow it through the system
- **Tenant-Aware Repositories**: Enforce tenant isolation at the data access layer
- **Row-Level Security (RLS)**: Database-level tenant isolation using PostgreSQL RLS
- **Per-Tenant Rate Limiting**: Rate limits scoped per tenant with different limits per tier
- **Per-Tenant Quota Management**: Quotas for requests, jobs, storage, and query cost per tenant

## Installation

```bash
npm install
```

## Prerequisites

- Node.js 18+
- PostgreSQL 12+ (for RLS examples)
- Redis (optional, for distributed rate limiting)

## Build

```bash
npm run build
```

## Running Examples

### Tenant Context Example

Demonstrates how tenant ID is extracted from requests and flows through the system.

```bash
npm run dev -- examples/tenant-context-example.ts
```

Then test with:

```bash
# With tenant ID in header
curl -H "X-Tenant-Id: tenant-1" http://localhost:3001/api/data

# Without tenant ID (should fail)
curl http://localhost:3001/api/data
```

### Tenant Repository Example

Demonstrates tenant-aware repositories that automatically filter queries by tenant.

```bash
npm run dev -- examples/tenant-repository-example.ts
```

Shows:
- Repositories require tenant ID in constructor
- All queries automatically include tenant filter
- Impossible to query without tenant context

### Row-Level Security Example

Demonstrates PostgreSQL RLS for database-level tenant isolation.

```bash
npm run dev -- examples/row-level-security-example.ts
```

**Setup RLS:**

1. Create database and tables:
```sql
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_orders_tenant_id ON orders(tenant_id);
```

2. Run RLS migration (see `src/row-level-security.ts` for SQL)

3. Test with example

### Rate Limiting Example

Demonstrates per-tenant rate limiting with different limits per tier.

```bash
npm run dev -- examples/rate-limiting-example.ts
```

Shows:
- In-memory rate limiting (for single-server)
- Redis-based rate limiting (for distributed)
- Different limits for free/standard/enterprise tiers

## Running the Full Server

The main server demonstrates all patterns working together:

```bash
npm run dev
```

The server exposes:

- `GET /api/orders` - Get orders for tenant (with rate limiting and quota checking)
- `GET /api/orders/:orderId` - Get specific order for tenant
- `POST /api/orders` - Create order for tenant
- `GET /api/metrics` - Get tenant metrics (rate limits, quotas)
- `GET /health` - Health check

### Example Requests

```bash
# Get orders for tenant-1
curl -H "X-Tenant-Id: tenant-1" http://localhost:3000/api/orders

# Create order for tenant-1
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: tenant-1" \
  -d '{"userId": "user-123", "amount": 100, "status": "pending"}'

# Get metrics for tenant-1
curl -H "X-Tenant-Id: tenant-1" http://localhost:3000/api/metrics
```

### Example Response (Rate Limited)

```json
{
  "error": "Rate limit exceeded",
  "retryAfter": 45,
  "limit": 100
}
```

HTTP Status: 429
Header: `Retry-After: 45`

### Example Response (Quota Exceeded)

```json
{
  "error": "Quota exceeded",
  "resource": "requests",
  "retryAfter": 30,
  "upgradeMessage": "Upgrade to increase quota"
}
```

HTTP Status: 429

## Code Structure

```
src/
  ├── types.ts                    # Core types (TenantContext, Tenant, Order, etc.)
  ├── tenant-context.ts          # Tenant ID extraction and context propagation
  ├── tenant-repository.ts       # Tenant-aware repository pattern
  ├── row-level-security.ts      # PostgreSQL RLS implementation
  ├── rate-limiter.ts            # Per-tenant rate limiting
  ├── quota-manager.ts           # Per-tenant quota management
  └── index.ts                   # Main server demonstrating all patterns

examples/
  ├── tenant-context-example.ts      # Tenant context propagation
  ├── tenant-repository-example.ts   # Tenant-aware repositories
  ├── row-level-security-example.ts   # PostgreSQL RLS
  └── rate-limiting-example.ts       # Per-tenant rate limiting
```

## Key Patterns

### 1. Tenant Context Propagation

Tenant ID enters the system via:
- JWT token (after authentication)
- API key header
- Subdomain
- X-Tenant-Id header
- Path parameter

Tenant context flows through middleware and is attached to request object.

### 2. Tenant-Aware Repositories

Repositories require tenant ID in constructor. All queries automatically include tenant filter. Impossible to query without tenant context.

### 3. Row-Level Security (RLS)

PostgreSQL RLS enforces tenant isolation at database level. Even buggy code can't access wrong tenant's data. Set tenant context before queries.

### 4. Per-Tenant Rate Limiting

Rate limits are scoped per tenant, not global. Different tenant tiers have different limits. Use Redis for distributed deployments.

### 5. Per-Tenant Quota Management

Quotas tracked per tenant for:
- Requests per minute
- Jobs per minute
- Storage size
- Query cost per month

## Testing

### Test Tenant Isolation

```bash
# Terminal 1: Start server
npm run dev

# Terminal 2: Send requests as different tenants
for tenant in tenant-1 tenant-2 tenant-3; do
  echo "Testing $tenant:"
  curl -H "X-Tenant-Id: $tenant" http://localhost:3000/api/orders
  echo ""
done
```

### Test Rate Limiting

```bash
# Send many requests to hit rate limit
for i in {1..150}; do
  curl -H "X-Tenant-Id: tenant-3" http://localhost:3000/api/orders
  echo ""
done
```

Watch for 429 responses after hitting the limit.

## Database Setup

### Create Tables

```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  tier VARCHAR(50) NOT NULL,
  subdomain VARCHAR(255),
  api_key VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  user_id UUID NOT NULL REFERENCES users(id),
  amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_orders_tenant_id ON orders(tenant_id);
```

### Enable Row-Level Security

See `src/row-level-security.ts` for RLS migration SQL.

## Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=saas_db
DB_USER=postgres
DB_PASSWORD=postgres

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# Server
PORT=3000
```

## Best Practices

1. **Always require tenant ID** - Make it impossible to forget
2. **Enforce at multiple layers** - Code, ORM, and database
3. **Use RLS for defense in depth** - Even buggy code is safe
4. **Rate limit per tenant** - Not globally
5. **Monitor per tenant** - Identify noisy neighbors
6. **Quota per tenant** - Prevent resource exhaustion
7. **Log with tenant ID** - Every log entry should include tenant
8. **Metrics per tenant** - Track performance per tenant

## Migration Path

1. **Phase 1**: Add tenant_id to all tables, introduce tenant context
2. **Phase 2**: Enforce tenant filters in code, enable RLS
3. **Phase 3**: Move high-value tenants to isolated infrastructure

## License

MIT

