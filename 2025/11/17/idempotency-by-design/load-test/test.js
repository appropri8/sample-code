import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // Ramp up to 50 users
    { duration: '1m', target: 50 },    // Stay at 50 users
    { duration: '30s', target: 100 },  // Ramp up to 100 users
    { duration: '1m', target: 100 },   // Stay at 100 users
    { duration: '30s', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.01'],    // Less than 1% of requests should fail
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';

export default function () {
  // Generate idempotency key per virtual user and iteration
  // This simulates a client that retries with the same key
  const idempotencyKey = `test-${__VU}-${__ITER}`;
  
  const payload = JSON.stringify({
    userId: `user-${randomString(8)}`,
    amount: Math.floor(Math.random() * 1000) + 100,
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey,
    },
    tags: { name: 'CreateOrder' },
  };
  
  // First request
  const res1 = http.post(`${BASE_URL}/orders`, payload, params);
  
  check(res1, {
    'first request status is 201': (r) => r.status === 201,
    'first request has order id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.id !== undefined;
      } catch (e) {
        return false;
      }
    },
  });
  
  // Small delay to simulate network delay
  sleep(0.1);
  
  // Retry with same idempotency key
  const res2 = http.post(`${BASE_URL}/orders`, payload, params);
  
  check(res2, {
    'retry status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    'retry returns same order id': (r) => {
      try {
        const body1 = JSON.parse(res1.body);
        const body2 = JSON.parse(r.body);
        return body1.id === body2.id;
      } catch (e) {
        return false;
      }
    },
  });
  
  // Test concurrent duplicates
  if (__ITER % 10 === 0) {
    const concurrentKey = `concurrent-${__VU}-${__ITER}`;
    const concurrentPayload = JSON.stringify({
      userId: `user-${randomString(8)}`,
      amount: Math.floor(Math.random() * 1000) + 100,
    });
    
    const concurrentParams = {
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': concurrentKey,
      },
      tags: { name: 'ConcurrentDuplicate' },
    };
    
    // Send 5 concurrent requests with same key
    const responses = [];
    for (let i = 0; i < 5; i++) {
      responses.push(http.post(`${BASE_URL}/orders`, concurrentPayload, concurrentParams));
    }
    
    // All should return same order ID
    const orderIds = responses
      .map(r => {
        try {
          return JSON.parse(r.body).id;
        } catch (e) {
          return null;
        }
      })
      .filter(id => id !== null);
    
    const uniqueIds = new Set(orderIds);
    check(null, {
      'concurrent duplicates return same id': () => uniqueIds.size === 1,
    });
  }
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  // Simple text summary
  return `
Test Summary:
  Total requests: ${data.metrics.http_reqs.values.count}
  Failed requests: ${data.metrics.http_req_failed.values.rate * 100}%
  Average duration: ${data.metrics.http_req_duration.values.avg}ms
  P95 duration: ${data.metrics.http_req_duration.values['p(95)']}ms
`;
}

