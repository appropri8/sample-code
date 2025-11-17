# Load Test for Idempotency

k6 load test that verifies idempotency behavior under load.

## Setup

Install k6:
```bash
# macOS
brew install k6

# Linux
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

## Run Tests

```bash
# Basic test
k6 run test.js

# With custom base URL
BASE_URL=http://localhost:3000 k6 run test.js

# With more virtual users
k6 run --vus 200 --duration 5m test.js
```

## What It Tests

1. **Idempotency:** Same key returns same result
2. **Retries:** Retrying with same key works correctly
3. **Concurrent duplicates:** Multiple requests with same key return same result
4. **Performance:** Response times under load

## Test Scenarios

- **Normal requests:** Each VU sends requests with unique keys
- **Retries:** Each VU retries with same key
- **Concurrent duplicates:** Every 10th iteration sends 5 concurrent requests with same key

## Expected Results

- All retries should return same order ID
- Concurrent duplicates should return same order ID
- 95% of requests should complete in < 500ms
- Less than 1% of requests should fail

