# Adaptive Load Shedding Samples

Complete executable code samples for the article [Designing Adaptive Load Shedding: Stop Protecting Services with Static Rate Limits Alone](https://appropri8.io/blog/2026/07/06/adaptive-load-shedding/).

## Structure

```
.
├── adaptive_load_shedding/
│   ├── middleware.py        # In-flight request limiter
│   ├── adaptive_limiter.py  # Adaptive concurrency control
│   └── retry.py             # Client backoff and retry
├── examples/
│   └── demo.py              # Runnable simulation
├── tests/
│   └── test_adaptive.py     # Unit tests
└── requirements.txt         # Python dependencies
```

## Quick Start

### 1. Run the demo

```bash
cd 2026/07/06/adaptive-load-shedding
python examples/demo.py
```

### 2. Run tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Key Samples

### In-Flight Request Limiter

`adaptive_load_shedding/middleware.py` counts active requests and rejects with a 503 when capacity is reached. It's the static foundation that adaptive control builds on.

### Adaptive Concurrency Control

`adaptive_load_shedding/adaptive_limiter.py` dynamically adjusts the concurrency limit based on observed latency. If latency exceeds 150% of target, it drops the limit by 10%. If latency drops below 80% of target, it increases the limit by 5%.

### Client Retry with Backoff and Jitter

`adaptive_load_shedding/retry.py` implements exponential backoff with full jitter. It refuses to retry non-idempotent requests (mutating POSTs without idempotency keys), aligning with AWS recommendations.

## License

MIT
