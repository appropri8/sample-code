# Project Structure

This document outlines the complete structure of the prompt caching code samples.

## Directory Structure

```
prompt-caching-llms/
├── README.md                          # Main documentation
├── requirements.txt                   # Python dependencies
├── .gitignore                        # Git ignore patterns
├── .env.example                      # Example environment variables
│
├── src/                              # Source code
│   ├── __init__.py
│   ├── simple_response_cache.py      # Basic Redis caching
│   ├── prompt_normalization.py       # Prompt normalization utilities
│   ├── semantic_cache.py             # Embedding-based semantic caching
│   ├── multi_layer_cache.py          # Multi-layer cache (L1/L2/L3)
│   ├── cache_metrics.py              # Metrics tracking and reporting
│   ├── anthropic_caching.py          # Anthropic-specific examples
│   ├── openai_caching.py             # OpenAI caching patterns
│   └── benchmark.py                  # Performance benchmarks
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── test_normalization.py         # Tests for normalization
│   └── test_metrics.py               # Tests for metrics
│
└── data/                             # Sample data
    └── sample_queries.json           # Sample queries for testing
```

## Source Files

### Core Caching

1. **simple_response_cache.py** (160 lines)
   - Basic Redis-based response caching
   - Hit/miss tracking
   - Cost savings calculation
   - Demo with statistics

2. **semantic_cache.py** (250 lines)
   - Embedding-based similarity matching
   - Configurable similarity threshold
   - Comparison with exact matching
   - Uses sentence-transformers

3. **multi_layer_cache.py** (280 lines)
   - L1: In-memory cache
   - L2: Redis cache
   - L3: Semantic cache
   - Cache promotion
   - Per-layer metrics

### Utilities

4. **prompt_normalization.py** (220 lines)
   - Whitespace normalization
   - JSON key sorting
   - List ordering
   - PromptBuilder class
   - Demonstrations

5. **cache_metrics.py** (370 lines)
   - Hit/miss tracking
   - Latency measurement
   - Token savings calculation
   - Cost analysis
   - Comprehensive reporting
   - Projection calculations

### Provider Examples

6. **anthropic_caching.py** (200 lines)
   - Explicit prompt caching with `cache_control`
   - Basic system prompt caching
   - Multi-turn conversation caching
   - Large context document caching

7. **openai_caching.py** (230 lines)
   - Application-level caching for OpenAI
   - Cache wrapper class
   - Stable system prompt patterns
   - Cache key sensitivity demos

### Benchmarks

8. **benchmark.py** (240 lines)
   - No cache vs response cache vs prompt cache
   - Performance comparison
   - Scalability testing
   - Cost and latency metrics

## Test Files

1. **test_normalization.py** (140 lines)
   - Whitespace normalization tests
   - JSON normalization tests
   - List normalization tests
   - PromptBuilder tests
   - Full coverage of normalization utilities

2. **test_metrics.py** (160 lines)
   - Metrics tracking tests
   - Hit ratio calculation tests
   - Latency calculation tests
   - Cost savings tests
   - Report structure validation

## Data Files

1. **sample_queries.json**
   - 10 sample queries
   - Categories: programming, support, policy, sales, technical
   - Expected token counts
   - Used in demos and benchmarks

## Running the Examples

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Run Individual Examples
```bash
python src/simple_response_cache.py
python src/prompt_normalization.py
python src/semantic_cache.py
python src/multi_layer_cache.py
python src/cache_metrics.py
python src/benchmark.py

# Provider-specific (requires API keys)
python src/anthropic_caching.py
python src/openai_caching.py
```

### Run Tests
```bash
pytest
pytest --cov=src tests/
```

## Key Features

### 1. Simple Response Cache
- Redis-based full response caching
- Exact match only
- Fast lookups (1-2ms)
- Easy to implement

### 2. Semantic Cache
- Similarity-based matching
- Catches paraphrases
- Higher hit rate than exact matching
- Requires embedding model

### 3. Multi-Layer Cache
- Three-tier caching strategy
- L1: Memory (fastest, 0.1ms)
- L2: Redis (fast, 1-2ms)
- L3: Semantic (flexible, 10-20ms)
- Automatic promotion

### 4. Metrics & Monitoring
- Hit ratio tracking
- Cost savings calculation
- Latency reduction measurement
- Token usage analytics
- Comprehensive reporting

### 5. Normalization
- Whitespace handling
- JSON key sorting
- List ordering
- Consistent hashing
- Higher cache hit rates

### 6. Provider Integration
- Anthropic explicit caching
- OpenAI application-level caching
- Real-world patterns
- Best practices

## Dependencies

- `redis` - Redis client
- `openai` - OpenAI API
- `anthropic` - Anthropic API
- `sentence-transformers` - Embeddings
- `numpy` - Numerical operations
- `pytest` - Testing framework
- `python-dotenv` - Environment variables

## Total Code

- **Source code**: ~1,900 lines
- **Tests**: ~300 lines
- **Documentation**: ~200 lines
- **Total**: ~2,400 lines of working code

All examples are runnable and demonstrate real caching patterns used in production.
