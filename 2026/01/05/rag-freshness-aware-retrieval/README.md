# RAG That Doesn't Rot: Freshness-Aware Retrieval

A complete Python implementation demonstrating how to build RAG systems that stay accurate when content changes. Includes incremental indexing, freshness-aware retrieval, and evaluation harness.

## Overview

This repository shows how to:
- Use incremental ingestion (only re-embed changed chunks)
- Track content hashes and last-modified timestamps
- Handle deleted content with tombstones
- Version chunks with metadata
- Rerank results using relevance + freshness + source priority
- Require citations and refuse weak context
- Evaluate freshness with test sets

## Features

- **Incremental Ingestion**: Only re-embed documents when content hash changes
- **Freshness-Aware Retrieval**: Rerank results considering relevance, recency, and source priority
- **Evaluation Harness**: Measure stale citation rate and top-k hit rate
- **12 Sample Documents**: Includes v1/v2 versions to demonstrate staleness
- **Complete Pipeline**: From ingestion to retrieval to evaluation

## Installation

```bash
pip install -r requirements.txt
```

Set your OpenAI API key (optional, for embedding generation):

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### 1. Incremental Ingestion

```bash
python src/incremental_ingestion.py --source-dir sample_docs
```

This will:
- Crawl documents in `sample_docs/`
- Compute content hashes
- Only re-embed when hash changes
- Store metadata (published_at, indexed_at, version)

### 2. Freshness-Aware Retrieval

```bash
python src/freshness_retrieval.py --query "What's our refund policy?"
```

This will:
- Retrieve top N by relevance
- Compute freshness scores
- Rerank with combined scores
- Return results with citations

### 3. Evaluation Harness

```bash
python src/evaluation_harness.py --test-set tests/freshness_test_set.jsonl
```

This will:
- Load test questions with expected doc IDs
- Measure stale citation rate
- Measure top-k hit rate
- Print evaluation report

## Project Structure

```
.
├── src/
│   ├── incremental_ingestion.py    # Incremental indexing with content hashing
│   ├── freshness_retrieval.py      # Freshness-aware retrieval and reranking
│   ├── evaluation_harness.py       # Evaluation with freshness test set
│   ├── document_tracker.py         # Content hashing and version tracking
│   ├── reranker.py                 # Reranking with freshness scores
│   └── vector_index.py             # Simple in-memory vector index
├── sample_docs/
│   ├── v1/                         # Original document versions
│   └── v2/                         # Updated document versions
├── tests/
│   ├── freshness_test_set.jsonl    # Test questions with expected answers
│   └── test_*.py                   # Unit tests
├── requirements.txt
└── README.md
```

## How to Simulate Doc Updates Locally

The repository includes 12 sample documents with intentional v1/v2 updates to demonstrate the "rot" problem.

### Step 1: Index Initial Documents (v1)

```bash
# Index v1 documents
python src/incremental_ingestion.py --source-dir sample_docs/v1 --index-file index_v1.pkl
```

### Step 2: Test Retrieval with v1

```bash
# Query with v1 index
python src/freshness_retrieval.py --query "What's our refund policy?" --index-file index_v1.pkl
```

You'll see results from v1 documents (e.g., "30 days" refund policy).

### Step 3: Update Documents (v2)

```bash
# Index v2 documents (simulates document updates)
python src/incremental_ingestion.py --source-dir sample_docs/v2 --index-file index_v2.pkl
```

### Step 4: Test Retrieval with v2

```bash
# Query with v2 index
python src/freshness_retrieval.py --query "What's our refund policy?" --index-file index_v2.pkl
```

You'll see results from v2 documents (e.g., "60 days" refund policy).

### Step 5: Compare Results

```bash
# Run evaluation to see the difference
python src/evaluation_harness.py --index-file index_v1.pkl --test-set tests/freshness_test_set.jsonl
python src/evaluation_harness.py --index-file index_v2.pkl --test-set tests/freshness_test_set.jsonl
```

The evaluation will show:
- Stale citation rate (how often old docs are retrieved)
- Top-k hit rate (how often expected docs are in top-k)
- Answer accuracy (whether answers match expected content)

### Simulating Incremental Updates

To simulate real-world incremental updates:

1. Start with v1 documents indexed
2. Copy v2 documents over v1 (simulating updates)
3. Run incremental ingestion again
4. The system will detect changes via content hashing
5. Only changed documents will be re-embedded

```bash
# Start with v1
cp -r sample_docs/v1/* sample_docs/current/

# Index v1
python src/incremental_ingestion.py --source-dir sample_docs/current --index-file index.pkl

# Simulate update: copy v2 over v1
cp sample_docs/v2/refund-policy.md sample_docs/current/refund-policy.md

# Run incremental ingestion (only refund-policy.md will be re-embedded)
python src/incremental_ingestion.py --source-dir sample_docs/current --index-file index.pkl
```

## Sample Documents

The repository includes 12 sample documents with v1/v2 versions:

1. **refund-policy.md**: 30 days (v1) → 60 days (v2)
2. **shipping-rates.md**: $4.99 (v1) → $5.99 (v2)
3. **return-policy.md**: 14 days (v1) → 21 days (v2)
4. **warranty.md**: 1 year (v1) → 2 years (v2)
5. **privacy-policy.md**: GDPR v1 → GDPR v2 (updated sections)
6. **terms-of-service.md**: Terms v1 → Terms v2 (updated clauses)
7. **product-catalog.md**: 10 products (v1) → 15 products (v2)
8. **api-documentation.md**: API v1 → API v2 (new endpoints)
9. **faq.md**: 5 questions (v1) → 8 questions (v2)
10. **support-guide.md**: Guide v1 → Guide v2 (updated procedures)
11. **pricing.md**: Pricing v1 → Pricing v2 (updated tiers)
12. **onboarding.md**: Onboarding v1 → Onboarding v2 (new steps)

Each document demonstrates a different type of update:
- Policy changes (refund, shipping, return, warranty)
- Content additions (product catalog, FAQ)
- Content updates (privacy, terms, API docs)
- Process changes (support, onboarding, pricing)

## Code Samples

### 1. Incremental Ingestion

See `src/incremental_ingestion.py` for:
- Content hashing to detect changes
- Only re-embedding changed documents
- Metadata tracking (published_at, indexed_at, version)
- Tombstone handling for deleted documents

### 2. Freshness-Aware Retrieval

See `src/freshness_retrieval.py` for:
- Query rewriting
- Hybrid search (keyword + vector)
- Freshness score computation
- Reranking with combined scores
- Citation generation

### 3. Evaluation Harness

See `src/evaluation_harness.py` for:
- JSONL test set loading
- Stale citation rate measurement
- Top-k hit rate calculation
- Answer accuracy checking
- Evaluation report generation

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

Run specific test:

```bash
pytest tests/test_incremental_ingestion.py
```

## Metrics

The evaluation harness tracks:
- **Citation Accuracy**: Percentage of queries where retrieved doc matches expected doc
- **Stale Citation Rate**: Percentage of queries where retrieved doc is stale (older than threshold)
- **Top-K Hit Rate**: Percentage of queries where expected doc is in top-k results
- **Answer Change Rate**: Percentage of queries where answer changes after doc update

## Best Practices

1. **Incremental Indexing**: Only re-embed when content hash changes
2. **Freshness Tracking**: Store published_at, indexed_at, version for each chunk
3. **Tombstones**: Mark deleted documents, don't retrieve them
4. **Reranking**: Combine relevance, freshness, and source priority
5. **Citations**: Require citations for key claims
6. **Refusal**: Refuse when context is weak
7. **Evaluation**: Test with freshness test sets
8. **Monitoring**: Track stale citation rates in production

## License

This code is provided as example code for educational purposes.
