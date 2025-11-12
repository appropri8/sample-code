"""Example demonstrating token tracking and cost monitoring"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rag_pipeline import RAGPipeline
from src.vector_store import SimpleVectorStore
from src.chunking import chunk_text
from src.embeddings import generate_embeddings
from src.monitoring import RAGLogger, count_tokens


def main():
    # Sample documents
    documents = [
        {
            "text": "Python error handling uses try-except blocks. The try block contains code that might raise an exception. The except block handles the exception.",
            "metadata": {"source": "doc1.md", "topic": "error_handling"}
        },
        {
            "text": "Context windows in LLMs have limits. GPT-4 supports 128k tokens. You need to manage context windows carefully in RAG applications.",
            "metadata": {"source": "doc2.md", "topic": "context_management"}
        }
    ]
    
    # Setup
    all_chunks = []
    for doc in documents:
        chunks = chunk_text(doc["text"], chunk_size=100, overlap=10)
        for chunk in chunks:
            chunk["metadata"] = doc["metadata"]
        all_chunks.extend(chunks)
    
    embeddings = generate_embeddings(all_chunks)
    vector_store = SimpleVectorStore()
    vector_store.add_chunks(all_chunks, embeddings)
    
    # Create pipeline with logger
    pipeline = RAGPipeline(vector_store=vector_store, max_context_tokens=5000)
    logger = RAGLogger("example_logs.jsonl")
    
    # Run multiple queries
    queries = [
        "How do I handle errors in Python?",
        "What are context window limits?",
        "Explain RAG applications"
    ]
    
    print("Running queries and tracking tokens...\n")
    
    for query in queries:
        print(f"Query: {query}")
        result = pipeline.generate(query, top_k=2)
        
        # Log the request
        logger.log_request(
            query=query,
            retrieved_chunks=all_chunks[:result['chunks_used']],
            response=result['answer'],
            token_counts={
                "prompt_tokens": result['prompt_tokens'],
                "completion_tokens": result['completion_tokens'],
                "total_tokens": result['total_tokens']
            },
            cost=result['cost'],
            latency=result['latency']
        )
        
        print(f"  Tokens: {result['total_tokens']} (prompt: {result['prompt_tokens']}, completion: {result['completion_tokens']})")
        print(f"  Cost: ${result['cost']:.4f}")
        print(f"  Latency: {result['latency']:.2f}s\n")
    
    # Get statistics
    stats = logger.get_stats()
    print("Overall Statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Total cost: ${stats['total_cost']:.4f}")
    print(f"  Average latency: {stats['avg_latency_ms']:.2f}ms")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    main()

