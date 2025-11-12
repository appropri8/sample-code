"""Basic RAG pipeline example"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rag_pipeline import RAGPipeline
from src.vector_store import SimpleVectorStore
from src.chunking import chunk_text
from src.embeddings import generate_embeddings


def main():
    # Sample documents
    documents = [
        {
            "text": """
            Python error handling is done using try-except blocks. The try block contains code that might raise an exception.
            The except block handles the exception. You can catch specific exceptions or use a general Exception handler.
            
            Example:
            try:
                result = 10 / 0
            except ZeroDivisionError:
                print("Cannot divide by zero")
            
            You can also use else and finally clauses. The else block runs if no exception occurs.
            The finally block always runs, regardless of whether an exception occurred.
            """,
            "metadata": {
                "source": "python_guide.md",
                "doc_type": "technical",
                "topic": "error_handling"
            }
        },
        {
            "text": """
            Context windows in LLMs have limits. GPT-4 supports up to 128,000 tokens.
            Claude 3 Opus supports up to 200,000 tokens. Each token costs money.
            
            When building RAG applications, you need to manage context windows carefully.
            Retrieve only relevant chunks. Budget your tokens. Cache embeddings.
            
            Best practices:
            - Use 500-1000 token chunks
            - Overlap chunks by 10-20%
            - Filter retrieved chunks by similarity
            - Monitor token usage and costs
            """,
            "metadata": {
                "source": "rag_guide.md",
                "doc_type": "technical",
                "topic": "context_management"
            }
        }
    ]
    
    # Chunk documents
    print("Chunking documents...")
    all_chunks = []
    for doc in documents:
        chunks = chunk_text(doc["text"], chunk_size=200, overlap=20)
        # Add metadata
        for chunk in chunks:
            chunk["metadata"] = doc["metadata"]
        all_chunks.extend(chunks)
    
    print(f"Created {len(all_chunks)} chunks")
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = generate_embeddings(all_chunks)
    
    # Create vector store
    print("Indexing in vector store...")
    vector_store = SimpleVectorStore()
    vector_store.add_chunks(all_chunks, embeddings)
    
    # Create RAG pipeline
    print("Creating RAG pipeline...")
    pipeline = RAGPipeline(
        vector_store=vector_store,
        model="gpt-4",
        max_context_tokens=10000
    )
    
    # Query
    query = "How do I handle errors in Python?"
    print(f"\nQuery: {query}")
    print("Generating response...\n")
    
    result = pipeline.generate(query, top_k=3)
    
    print(f"Answer: {result['answer']}\n")
    print(f"Chunks used: {result['chunks_used']}")
    print(f"Prompt tokens: {result['prompt_tokens']}")
    print(f"Completion tokens: {result['completion_tokens']}")
    print(f"Total tokens: {result['total_tokens']}")
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Latency: {result['latency']:.2f}s")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    main()

