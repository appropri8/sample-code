# Prompt Caching in LLMs - Code Examples

This repository contains working code examples for the article "Prompt Caching in Large Language Models: Reducing Latency and Cost Without Changing Your Application Logic".

## Overview

These examples demonstrate different prompt caching strategies:

1. **Simple Response Cache** - Redis-based full response caching
2. **Prompt Normalization** - Tools to normalize prompts for better cache hits
3. **Semantic Cache** - Embedding-based similarity matching
4. **Multi-Layer Cache** - Combining response and prompt caching
5. **Cache Metrics** - Measuring cache effectiveness
6. **Provider Examples** - Anthropic and OpenAI caching patterns
7. **Benchmarks** - Performance comparison

## Setup

### Requirements

- Python 3.9+
- Redis (for caching examples)
- OpenAI API key (for OpenAI examples)
- Anthropic API key (for Anthropic examples)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (if not already running)
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis
```

### Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Examples

### 1. Simple Response Cache

```bash
python src/simple_response_cache.py
```

Demonstrates basic response caching with Redis. Measures hit ratio and latency.

### 2. Prompt Normalization

```bash
python src/prompt_normalization.py
```

Shows how to normalize prompts for consistent cache hits:
- Whitespace normalization
- JSON key sorting
- Stable list ordering

### 3. Semantic Cache

```bash
python src/semantic_cache.py
```

Uses embeddings to match similar prompts. Allows semantic similarity matching beyond exact text matches.

### 4. Multi-Layer Cache

```bash
python src/multi_layer_cache.py
```

Combines multiple caching strategies for maximum efficiency.

### 5. Cache Metrics

```bash
python src/cache_metrics.py
```

Tracks and reports cache performance metrics:
- Hit ratio
- Cost savings
- Latency reduction

### 6. Provider Examples

```bash
# Anthropic explicit caching
python src/anthropic_caching.py

# OpenAI patterns
python src/openai_caching.py
```

### 7. Benchmark

```bash
python src/benchmark.py
```

Compares different caching strategies:
- No cache
- Response cache
- Prompt cache (simulated)

## Project Structure

```
prompt-caching-llms/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── src/
│   ├── __init__.py
│   ├── simple_response_cache.py
│   ├── prompt_normalization.py
│   ├── semantic_cache.py
│   ├── multi_layer_cache.py
│   ├── cache_metrics.py
│   ├── anthropic_caching.py
│   ├── openai_caching.py
│   └── benchmark.py
├── tests/
│   ├── __init__.py
│   ├── test_normalization.py
│   └── test_metrics.py
└── data/
    └── sample_queries.json
```

## Key Concepts

### Cache Hit vs Miss

- **Cache Hit**: Prompt found in cache, response returned immediately (fast, cheap)
- **Cache Miss**: Prompt not in cache, LLM processes it (slow, expensive)

### Prompt Design for Caching

```python
# Bad: Dynamic variable at start
f"User {user_id} asks: {question}"

# Good: Dynamic variable at end
f"Question: {question}\nUser ID: {user_id}"
```

### Cost Savings Formula

```python
cost_with_cache = (
    (hits * tokens * cost_per_token * 0.1) +  # Cache hits (10% cost)
    (misses * tokens * cost_per_token)         # Cache misses (100% cost)
)

savings = cost_without_cache - cost_with_cache
```

## Common Patterns

### 1. Stable System Prompts

```python
# Always use the same system prompt
SYSTEM_PROMPT = "You are a helpful assistant."

def make_prompt(user_question: str):
    return f"{SYSTEM_PROMPT}\n\nQuestion: {user_question}"
```

### 2. Version Your Prompts

```python
PROMPT_VERSION = "v2.1"
SYSTEM_PROMPT = f"[Version: {PROMPT_VERSION}] You are a helpful assistant."
```

### 3. Normalize Before Caching

```python
from src.prompt_normalization import normalize_prompt

normalized = normalize_prompt(raw_prompt)
cache_key = hash(normalized)
```

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_normalization.py

# Run with coverage
pytest --cov=src tests/
```

## Performance Tips

1. **Put static content first** - System prompts, instructions, context
2. **Put dynamic content last** - User queries, IDs, timestamps
3. **Avoid random elements** - UUIDs, random numbers, current timestamps
4. **Normalize JSON** - Sort keys, consistent formatting
5. **Version prompts** - Explicit versioning for cache invalidation

## Monitoring

Track these metrics in production:

- **Hit Ratio**: `hits / (hits + misses)` - Target: 60%+
- **Cost Savings**: `(no_cache_cost - with_cache_cost) / no_cache_cost` - Target: 50%+
- **Latency P50**: Median response time - Target: <500ms for hits
- **Eviction Rate**: How often cache entries are evicted - Target: <10%

## Troubleshooting

### Low Hit Ratio

- Check if prompts have stable prefixes
- Look for dynamic content at the start
- Verify normalization is working
- Check cache TTL settings

### High Memory Usage

- Reduce cache TTL
- Implement LRU eviction
- Monitor cache size
- Consider semantic caching for similar prompts

### Stale Responses

- Set appropriate TTL
- Implement cache invalidation
- Version prompts
- Monitor content freshness

## License

MIT

## Related

- [Article](https://appropri8.com/blog/2026/07/12/prompt-caching-llms/)
- [Anthropic Prompt Caching Docs](https://docs.anthropic.com/claude/docs/prompt-caching)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
