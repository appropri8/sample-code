# Efficient Context-Window Management for RAG Applications

A Python library for building efficient retrieval-augmented generation (RAG) pipelines with optimized context-window management. This library provides document chunking, embedding generation, vector storage, retrieval optimization, context budgeting, and cost monitoring.

## Features

- **Intelligent Chunking**: Split documents with configurable size, overlap, and semantic boundaries
- **Embedding Generation**: Generate and cache embeddings using OpenAI or other models
- **Vector Storage**: Simple in-memory vector store (extendable to Pinecone, Weaviate, etc.)
- **Retrieval Optimization**: Similarity search with filtering, ranking, and deduplication
- **Context Budgeting**: Manage token allocation across system prompts, context, and responses
- **Caching**: Cache embeddings and retrieval results to reduce costs
- **Token Tracking**: Monitor token usage and estimate costs
- **Summarization**: Summarize chunks when they exceed token budgets

## Installation

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Basic RAG Pipeline

```python
from src.rag_pipeline import RAGPipeline
from src.vector_store import SimpleVectorStore
from src.chunking import chunk_text
from src.embeddings import generate_embeddings

# Load and chunk documents
documents = ["Your long document text here..."]
chunks = []
for doc in documents:
    chunks.extend(chunk_text(doc, chunk_size=500, overlap=50))

# Generate embeddings
embeddings = generate_embeddings(chunks)

# Create vector store
vector_store = SimpleVectorStore()
vector_store.add_chunks(chunks, embeddings)

# Create RAG pipeline
pipeline = RAGPipeline(
    vector_store=vector_store,
    model="gpt-4",
    max_context_tokens=30000
)

# Query
result = pipeline.generate("What is error handling in Python?")
print(result["answer"])
print(f"Tokens used: {result['total_tokens']}")
print(f"Cost: ${result['cost']:.4f}")
```

### With Summarization

```python
from src.rag_pipeline import SummarizingRAGPipeline

# Use summarization pipeline for large contexts
pipeline = SummarizingRAGPipeline(
    vector_store=vector_store,
    model="gpt-4",
    max_context_tokens=30000
)

result = pipeline.generate("Explain Python error handling")
print(result["answer"])
```

## Architecture

### Components

1. **Chunking Module** (`src/chunking.py`): Split documents into chunks
   - Configurable chunk size and overlap
   - Token counting
   - Metadata preservation

2. **Embeddings Module** (`src/embeddings.py`): Generate text embeddings
   - OpenAI embeddings API
   - Embedding caching
   - Batch processing

3. **Vector Store** (`src/vector_store.py`): Store and search embeddings
   - Cosine similarity search
   - Metadata filtering
   - Top-K retrieval

4. **RAG Pipeline** (`src/rag_pipeline.py`): Main pipeline
   - Retrieval
   - Context budgeting
   - Prompt construction
   - LLM invocation
   - Token tracking

5. **Summarization** (`src/summarization.py`): Summarize chunks
   - Token budget management
   - Preserve key information

6. **Monitoring** (`src/monitoring.py`): Track usage and costs
   - Token counting
   - Cost estimation
   - Request logging

## Usage Examples

### Document Indexing

```python
from src.chunking import chunk_text
from src.embeddings import generate_embeddings
from src.vector_store import SimpleVectorStore

# Load documents
documents = load_documents("path/to/documents")

# Chunk documents
all_chunks = []
for doc in documents:
    chunks = chunk_text(
        doc["text"],
        chunk_size=500,
        overlap=50
    )
    # Add metadata
    for chunk in chunks:
        chunk["metadata"] = {
            "source": doc["filename"],
            "doc_type": doc["type"],
            "date": doc["date"]
        }
    all_chunks.extend(chunks)

# Generate embeddings
embeddings = generate_embeddings(all_chunks)

# Store in vector database
vector_store = SimpleVectorStore()
vector_store.add_chunks(all_chunks, embeddings)
```

### Querying with Context Budgeting

```python
from src.rag_pipeline import RAGPipeline

pipeline = RAGPipeline(
    vector_store=vector_store,
    model="gpt-4",
    max_context_tokens=30000  # Budget for context
)

result = pipeline.generate(
    query="How do I handle errors in Python?",
    top_k=5  # Retrieve top 5 chunks
)

print(f"Answer: {result['answer']}")
print(f"Chunks used: {result['chunks_used']}")
print(f"Total tokens: {result['total_tokens']}")
print(f"Estimated cost: ${result['cost']:.4f}")
```

### Advanced: Summarization for Large Contexts

```python
from src.rag_pipeline import SummarizingRAGPipeline

pipeline = SummarizingRAGPipeline(
    vector_store=vector_store,
    model="gpt-4",
    max_context_tokens=30000
)

# This will summarize chunks if they exceed the budget
result = pipeline.generate(
    query="Explain Python error handling comprehensively",
    top_k=10
)
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

### Test Categories

- **Unit Tests**: Test individual components
  - `test_chunking.py`: Document chunking
  - `test_embeddings.py`: Embedding generation
  - `test_vector_store.py`: Vector search
  - `test_rag_pipeline.py`: Pipeline functionality
  - `test_monitoring.py`: Token tracking and costs

- **Integration Tests**: Test full pipeline
  - `test_integration.py`: End-to-end RAG flow

## Best Practices

1. **Chunk Size**: Use 500-1000 tokens for most documents
   - Technical docs: 500-800 tokens
   - Legal docs: 800-1200 tokens
   - Code: 400-600 tokens

2. **Overlap**: Use 10-20% overlap between chunks
   - Prevents information loss at boundaries
   - Preserves context

3. **Context Budget**: Allocate 20-30% of context window for retrieved context
   - Reserve space for system prompts
   - Leave room for model responses

4. **Caching**: Cache embeddings (they don't change)
   - Cache retrieval results for common queries
   - Set appropriate TTLs

5. **Monitoring**: Track token usage and costs
   - Log all requests
   - Monitor trends
   - Set alerts for unusual usage

## Design Principles

This library implements best practices for context-window management:

1. **Intelligent Chunking**: Preserve semantic boundaries
2. **Efficient Retrieval**: Filter and rank results
3. **Context Budgeting**: Allocate tokens strategically
4. **Caching**: Reduce redundant API calls
5. **Monitoring**: Track usage and costs

## Cost Considerations

Token usage directly impacts costs. Monitor:
- **Prompt tokens**: Input to the model
- **Completion tokens**: Model output
- **Embedding tokens**: For embedding generation

Example costs (as of 2024, adjust for current rates):
- GPT-4: $0.03/1k prompt tokens, $0.06/1k completion tokens
- GPT-3.5 Turbo: $0.0015/1k prompt tokens, $0.002/1k completion tokens
- Embeddings: $0.0001/1k tokens (text-embedding-3-small)

## Limitations

- Simple vector store is in-memory (use Pinecone/Weaviate for production)
- Summarization adds latency and cost
- Token counting is approximate (actual usage may vary)
- Cost estimates are based on published pricing

## Contributing

When adding features:
1. Add tests for new functionality
2. Update documentation
3. Consider cost and performance implications
4. Test with various document types

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

## References

- [OpenAI Embeddings Documentation](https://platform.openai.com/docs/guides/embeddings)
- [Retrieval-Augmented Generation (RAG) - Wikipedia](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)
- [OpenAI Pricing](https://openai.com/pricing)

