import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const requestDuration = new Trend('request_duration');

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p95<500', 'p99<1000'],
    'errors': ['rate<0.01'],
    'request_duration': ['p95<500', 'p99<1000'],
  },
};

export default function () {
  const idempotencyKey = `test-${__VU}-${__ITER}-${Date.now()}`;
  const payload = JSON.stringify({
    userId: Math.floor(Math.random() * 1000),
    amount: Math.floor(Math.random() * 1000) + 10,
    status: 'pending'
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey,
    },
    tags: { name: 'CreateOrder' },
  };
  
  const startTime = Date.now();
  const res = http.post('http://localhost:3000/orders', payload, params);
  const duration = Date.now() - startTime;
  
  requestDuration.add(duration);
  
  const success = check(res, {
    'status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has order id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.id !== undefined;
      } catch {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  
  // 10% of requests retry with same idempotency key
  if (Math.random() < 0.1) {
    sleep(1);
    const retryRes = http.post('http://localhost:3000/orders', payload, params);
    const retrySuccess = check(retryRes, {
      'retry returns same result': (r) => {
        try {
          const originalBody = JSON.parse(res.body);
          const retryBody = JSON.parse(r.body);
          return originalBody.id === retryBody.id;
        } catch {
          return false;
        }
      },
    });
    errorRate.add(!retrySuccess);
  }
  
  // Occasionally read the order
  if (Math.random() < 0.3) {
    sleep(0.5);
    try {
      const orderBody = JSON.parse(res.body);
      const getRes = http.get(`http://localhost:3000/orders/${orderBody.id}`, {
        tags: { name: 'GetOrder' },
      });
      check(getRes, {
        'get order status is 200': (r) => r.status === 200,
      });
    } catch (e) {
      // Ignore if order creation failed
    }
  }
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': JSON.stringify(data, null, 2),
  };
}

