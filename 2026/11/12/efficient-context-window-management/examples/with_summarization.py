"""RAG pipeline with summarization example"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rag_pipeline import SummarizingRAGPipeline
from src.vector_store import SimpleVectorStore
from src.chunking import chunk_text
from src.embeddings import generate_embeddings


def main():
    # Sample long document
    long_document = """
    Python error handling is a fundamental aspect of writing robust code. When programs encounter unexpected situations,
    exceptions are raised. Python provides several mechanisms for handling exceptions.
    
    The try-except block is the primary mechanism. You wrap potentially problematic code in a try block.
    If an exception occurs, Python looks for a matching except block. You can catch specific exceptions
    like ZeroDivisionError, ValueError, or FileNotFoundError. Or you can catch the general Exception class.
    
    Example of specific exception handling:
    try:
        file = open('data.txt', 'r')
        content = file.read()
    except FileNotFoundError:
        print("File not found")
    except PermissionError:
        print("Permission denied")
    finally:
        file.close()
    
    The else clause runs if no exception occurs. The finally clause always runs, making it useful for cleanup.
    
    You can also raise your own exceptions using the raise keyword. This is useful for validating inputs
    or signaling error conditions in your code.
    
    Custom exceptions can be created by inheriting from the Exception class. This allows you to create
    domain-specific error types that make your code more readable and maintainable.
    
    Exception chaining allows you to preserve the original exception when raising a new one. This is done
    using the 'from' keyword: raise NewException from original_exception.
    
    Context managers (using the 'with' statement) automatically handle resource cleanup, reducing the need
    for explicit finally blocks in many cases.
    """
    
    # Chunk the document
    print("Chunking document...")
    chunks = chunk_text(long_document, chunk_size=300, overlap=30)
    print(f"Created {len(chunks)} chunks")
    
    # Add metadata
    for chunk in chunks:
        chunk["metadata"] = {
            "source": "python_error_handling.md",
            "doc_type": "technical"
        }
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = generate_embeddings(chunks)
    
    # Create vector store
    print("Indexing in vector store...")
    vector_store = SimpleVectorStore()
    vector_store.add_chunks(chunks, embeddings)
    
    # Create summarizing RAG pipeline
    print("Creating RAG pipeline with summarization...")
    pipeline = SummarizingRAGPipeline(
        vector_store=vector_store,
        model="gpt-4",
        max_context_tokens=5000  # Smaller budget to trigger summarization
    )
    
    # Query
    query = "Explain Python error handling comprehensively, including try-except, custom exceptions, and context managers"
    print(f"\nQuery: {query}")
    print("Generating response (with summarization if needed)...\n")
    
    result = pipeline.generate(query, top_k=5)
    
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

