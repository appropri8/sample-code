# Hero Diagram Reference

## Multi-Tenancy Architecture Diagram

This document describes the hero diagram for the article "Designing Safe Multi-Tenancy in Kubernetes for Internal Developer Platforms".

### Diagram Description

The diagram should show:

1. **Top Level: Internal Developer Platform (IDP)**
   - Platform team manages the cluster
   - Developers interact with the platform (not directly with Kubernetes)

2. **Middle Level: Kubernetes Cluster**
   - Single shared cluster
   - Multiple tenant namespaces (Team A, Team B, Team C, etc.)
   - Shared services namespace
   - Control plane (API server, etcd, scheduler)

3. **Isolation Layers (shown as boundaries around each tenant):**
   - **Identity & Access**: RBAC roles per namespace
   - **Network**: NetworkPolicy blocking cross-tenant traffic
   - **Resources**: ResourceQuota limiting CPU/memory per tenant
   - **Security**: Pod Security Standards enforced

4. **Bottom Level: Physical Infrastructure**
   - Shared nodes (all tenants' pods run here)
   - Node pools (optional, for compliance workloads)

### Visual Elements

- Use different colors for each tenant namespace
- Show NetworkPolicy as barriers between tenants
- Show ResourceQuota as limits/boundaries
- Show shared services as a separate namespace accessible by all tenants
- Use arrows to show:
  - Developers → Platform → Kubernetes
  - Tenants isolated from each other
  - Tenants can access shared services
  - All tenants share the same nodes

### ASCII Art Version (for reference)

```
┌─────────────────────────────────────────────────────────┐
│         Internal Developer Platform (IDP)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  Team A  │  │  Team B  │  │  Team C  │  ...          │
│  │ Developer│  │ Developer│  │ Developer│               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
└───────┼─────────────┼─────────────┼──────────────────────┘
        │             │             │
        ▼             ▼             ▼
┌─────────────────────────────────────────────────────────┐
│              Kubernetes Cluster (Shared)                 │
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Control Plane                        │  │
│  │  API Server | etcd | Scheduler | Controller      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Team A      │  │  Team B      │  │  Team C      │  │
│  │  Namespace   │  │  Namespace   │  │  Namespace   │  │
│  │              │  │              │  │              │  │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │  │
│  │ │   Pods   │ │  │ │   Pods   │ │  │ │   Pods   │ │  │
│  │ │          │ │  │ │          │ │  │ │          │ │  │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │  │
│  │              │  │              │  │              │  │
│  │ RBAC ✓      │  │ RBAC ✓      │  │ RBAC ✓      │  │
│  │ Network ✓   │  │ Network ✓   │  │ Network ✓   │  │
│  │ Quota ✓     │  │ Quota ✓     │  │ Quota ✓     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │          │
│         └─────────────────┼─────────────────┘          │
│                           │                             │
│                  ┌────────▼────────┐                    │
│                  │ Shared Services │                    │
│                  │   Namespace     │                    │
│                  │  (PostgreSQL,  │                    │
│                  │   Redis, etc.) │                    │
│                  └─────────────────┘                    │
│                                                           │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Physical Infrastructure                     │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  Node 1  │  │  Node 2  │  │  Node 3  │  ...          │
│  │          │  │          │  │          │               │
│  │ Team A   │  │ Team B   │  │ Team C   │               │
│  │ Pods     │  │ Pods     │  │ Pods     │               │
│  │          │  │          │  │          │               │
│  │ Team B   │  │ Team C   │  │ Team A   │               │
│  │ Pods     │  │ Pods     │  │ Pods     │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│                                                           │
│  (All tenants share the same physical nodes)              │
└─────────────────────────────────────────────────────────┘
```

### Key Points to Highlight

1. **Isolation**: Each tenant is isolated by namespace boundaries, RBAC, NetworkPolicy, and ResourceQuota
2. **Sharing**: All tenants share the same control plane and physical nodes
3. **Shared Services**: Common services (databases, queues) are accessible to all tenants
4. **Platform Layer**: Developers don't interact with Kubernetes directly; they use the IDP

### Design Notes

- Use a modern, clean design style
- Colors: Different shades for each tenant (e.g., blue for Team A, green for Team B, orange for Team C)
- Show isolation boundaries clearly (dashed lines or colored borders)
- Make it clear that nodes are shared (show pods from different tenants on the same node)
- Keep it simple and easy to understand at a glance
