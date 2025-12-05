# Control Plane vs Data Plane: Code Examples

This repository contains executable code samples demonstrating the control plane and data plane separation pattern.

## Structure

- `go/` - Go implementation of control plane and data plane
- `typescript/` - TypeScript implementation with examples
- `config/` - Example configuration files and schemas

## Quick Start

### Go Implementation

```bash
cd go
go mod download
go run control-plane/main.go
go run data-plane/main.go
```

### TypeScript Implementation

```bash
cd typescript
npm install
npm run build
npm start
```

## Components

### Control Plane

- Config API for managing rate limits, feature flags, and routing rules
- Reconciliation loop for pushing configs to data plane instances
- Audit logging for all config changes
- Version management for rollback support

### Data Plane

- Fast path rate limiting using local config cache
- Config watcher that subscribes to control plane updates
- Safe defaults when control plane is unavailable
- High-performance request handling

## Examples

See the `examples/` directory for:
- Creating and updating rate limit policies
- Config push and pull patterns
- Rollback scenarios
- Failure handling
