# Consumer-Driven Contract Testing: Complete Code Samples

Complete executable code samples demonstrating consumer-driven contract testing with Pact for microservices.

## Overview

This repository contains TypeScript/Node.js implementations of contract testing:

- **Consumer Tests**: OrderService defines contracts for BillingService
- **Provider Verification**: BillingService verifies it satisfies all consumer contracts
- **CI/CD Integration**: GitHub Actions workflows for automated contract testing
- **Contract Broker**: Examples of publishing and verifying contracts

## Architecture

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────────┐
│  Order Service  │────────▶│   Contract  │────────▶│ Billing Service │
│   (Consumer)    │         │   (Pact)     │         │   (Provider)    │
└─────────────────┘         └──────┬───────┘         └─────────────────┘
                                    │
                                    ▼
                            ┌─────────────────┐
                            │ Contract Broker │
                            │  (Pact Broker)  │
                            └─────────────────┘
```

## Prerequisites

- Node.js 18+ installed
- npm installed
- (Optional) Pact Broker running for contract management

## Installation

```bash
npm install
```

## Running Contract Tests

### Consumer Tests (OrderService)

Run contract tests from the consumer side:

```bash
npm run test:consumer
```

This will:
1. Start a mock BillingService using Pact
2. Run OrderService tests against the mock
3. Generate contract files in `./pacts/`

### Provider Verification (BillingService)

Start the provider service and verify contracts:

```bash
# Terminal 1: Start provider
npm run start:provider

# Terminal 2: Run verification
npm run test:provider
```

Or run both in one command (for testing):

```bash
npm run test:provider
```

The verification test will:
1. Start the real BillingService
2. Fetch contracts from broker (or local files)
3. Replay each interaction
4. Verify responses match contracts
5. Publish verification results

## Contract Files

Contracts are generated in `./pacts/` directory:

```
pacts/
  └── orderservice-billingservice.json
```

Example contract structure:

```json
{
  "consumer": {
    "name": "OrderService"
  },
  "provider": {
    "name": "BillingService"
  },
  "interactions": [
    {
      "description": "a request to create a payment",
      "providerState": "order exists and is valid",
      "request": {
        "method": "POST",
        "path": "/payments",
        "body": {
          "orderId": "order_123",
          "amount": 100.00,
          "currency": "USD"
        }
      },
      "response": {
        "status": 201,
        "body": {
          "paymentId": "pay_abc123",
          "status": "completed"
        }
      }
    }
  ]
}
```

## Publishing Contracts to Broker

If you have a Pact Broker running:

```bash
export PACT_BROKER_URL=http://localhost:9292
export PACT_BROKER_TOKEN=your-token
npm run publish:pacts
```

## CI/CD Integration

### Consumer Pipeline

The consumer pipeline (`.github/workflows/consumer-ci.yml`):

1. Runs contract tests
2. Generates contracts
3. Publishes contracts to broker (on main branch)

### Provider Pipeline

The provider pipeline (`.github/workflows/provider-ci.yml`):

1. Starts provider service
2. Fetches contracts from broker
3. Runs verification tests
4. Blocks deployment if verification fails
5. Deploys if verification passes

## Code Structure

```
src/
  ├── types.ts                    # TypeScript interfaces
  ├── consumer/
  │   └── order-service.ts        # OrderService implementation
  └── provider/
      └── billing-service.ts      # BillingService implementation

tests/
  ├── consumer/
  │   └── order-service.test.ts   # Consumer contract tests
  └── provider/
      └── billing-service.verification.test.ts  # Provider verification

.github/
  └── workflows/
      ├── consumer-ci.yml         # Consumer CI/CD pipeline
      └── provider-ci.yml         # Provider CI/CD pipeline

pacts/                              # Generated contract files
```

## Key Concepts

### 1. Consumer-Driven Contracts

Consumers define what they need. Providers verify they can satisfy those needs.

**Consumer test:**
```typescript
await provider.addInteraction({
  uponReceiving: 'a request to create a payment',
  withRequest: { method: 'POST', path: '/payments', body: {...} },
  willRespondWith: { status: 201, body: {...} },
});
```

**Provider verification:**
```typescript
const verifier = new Verifier({
  providerBaseUrl: 'http://localhost:3000',
  pactBrokerUrl: 'https://broker.example.com',
  provider: 'BillingService',
});
await verifier.verifyProvider();
```

### 2. Contract Versioning

Contracts are versioned with consumer versions. Providers verify against specific consumer versions.

```typescript
consumerVersionTags: ['main', 'v1.0.0']
```

### 3. Provider States

Provider states set up the provider's initial state before each interaction:

```typescript
state: 'order exists and is valid'
```

### 4. Flexible Matching

Use Pact matchers for flexible contract matching:

```typescript
Matchers.string('pay_abc123')  // Any string
Matchers.decimal(100.00)      // Any decimal
Matchers.iso8601DateTime()     // Any ISO8601 date
```

## Best Practices

1. **Test both happy and error paths** - Include error responses in contracts
2. **Use realistic data** - Contracts should reflect real API behavior
3. **Group scenarios by use case** - Don't create a contract for every variation
4. **Keep contracts business-focused** - Avoid internal implementation details
5. **Version contracts** - Track contract evolution over time
6. **Run tests on every commit** - Fast feedback catches issues early
7. **Gate deployments** - Block provider deployments if contracts fail

## Common Issues

### Contracts Not Matching

**Problem:** Provider verification fails with "Response does not match"

**Solution:**
- Check field names match exactly
- Verify data types match (string vs number)
- Ensure optional fields are handled correctly
- Check provider state setup

### Provider State Not Working

**Problem:** Provider state doesn't set up correctly

**Solution:**
- Verify provider state handlers are implemented
- Check state names match exactly
- Ensure state setup runs before interaction

### Contracts Not Publishing

**Problem:** Contracts don't appear in broker

**Solution:**
- Check PACT_BROKER_URL is correct
- Verify authentication token is valid
- Check network connectivity to broker
- Review broker logs for errors

## Setting Up Pact Broker (Optional)

For local development, use Docker:

```bash
docker run -d \
  --name pact-broker \
  -p 9292:9292 \
  -e PACT_BROKER_DATABASE_URL=postgres://pact:pact@postgres/pact \
  -e PACT_BROKER_BASIC_AUTH_USERNAME=pact \
  -e PACT_BROKER_BASIC_AUTH_PASSWORD=pact \
  pactfoundation/pact-broker
```

Or use [PactFlow](https://pactflow.io/) (managed service).

## Next Steps

- Add more consumer-provider pairs
- Implement contract versioning strategy
- Add contract change notifications
- Integrate with API documentation
- Add contract testing to more services
- Set up contract testing dashboard

## Resources

- [Pact Documentation](https://docs.pact.io/)
- [Consumer-Driven Contracts](https://martinfowler.com/articles/consumerDrivenContracts.html)
- [Contract Testing Best Practices](https://docs.pact.io/best_practices)
- [Pact Broker](https://github.com/pact-foundation/pact_broker)

## License

MIT

