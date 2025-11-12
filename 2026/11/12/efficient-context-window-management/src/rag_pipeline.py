"""RAG pipeline with context window management"""

from openai import OpenAI
import tiktoken
import time
import os
from typing import List, Dict, Optional

from .vector_store import SimpleVectorStore
from .embeddings import EmbeddingCache
from .monitoring import count_tokens, estimate_cost
from .summarization import summarize_chunk


class RAGPipeline:
    """RAG pipeline with context window budgeting"""
    
    def __init__(
        self,
        vector_store: SimpleVectorStore,
        embedding_cache: Optional[EmbeddingCache] = None,
        model: str = "gpt-4",
        max_context_tokens: int = 30000,
        system_prompt: str = "You are a helpful assistant. Answer questions based on the provided context."
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            vector_store: Vector store with indexed chunks
            embedding_cache: Optional embedding cache
            model: LLM model to use
            max_context_tokens: Maximum tokens for retrieved context
            system_prompt: System prompt for the LLM
        """
        self.vector_store = vector_store
        self.embedding_cache = embedding_cache or EmbeddingCache()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.max_context_tokens = max_context_tokens
        self.system_prompt = system_prompt
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding with caching."""
        cached = self.embedding_cache.get(text)
        if cached:
            return cached
        
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embedding = response.data[0].embedding
        self.embedding_cache.set(text, embedding)
        return embedding
    
    def retrieve_chunks(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """Retrieve relevant chunks."""
        query_embedding = self.generate_embedding(query)
        results = self.vector_store.search(
            query_embedding,
            top_k=top_k * 2,  # Retrieve more for filtering
            min_similarity=min_similarity
        )
        
        # Extract chunks (without similarity scores for now)
        chunks = [chunk for chunk, score in results[:top_k]]
        return chunks
    
    def build_prompt(
        self,
        query: str,
        chunks: List[Dict],
    ) -> str:
        """Build prompt with context budgeting."""
        # Count system prompt tokens
        system_tokens = len(self.encoding.encode(self.system_prompt))
        query_tokens = len(self.encoding.encode(query))
        
        # Reserve space for response (estimate 2000 tokens)
        reserved_tokens = 2000
        available_tokens = self.max_context_tokens - system_tokens - query_tokens - reserved_tokens
        
        # Add chunks until we hit the limit
        context_parts = []
        current_tokens = 0
        
        for chunk in chunks:
            chunk_text = chunk["text"]
            chunk_tokens = len(self.encoding.encode(chunk_text))
            
            if current_tokens + chunk_tokens > available_tokens:
                break
            
            context_parts.append(chunk_text)
            current_tokens += chunk_tokens
        
        context = "\n\n---\n\n".join(context_parts)
        
        prompt = f"""{self.system_prompt}

Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    def generate(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> Dict:
        """Generate response using RAG."""
        start_time = time.time()
        
        # Retrieve chunks
        chunks = self.retrieve_chunks(query, top_k=top_k, min_similarity=min_similarity)
        
        # Build prompt
        prompt = self.build_prompt(query, chunks)
        
        # Call LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        latency = time.time() - start_time
        
        # Calculate tokens and cost
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        cost = estimate_cost(prompt_tokens, completion_tokens, self.model)
        
        return {
            "answer": answer,
            "chunks_used": len(chunks),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "latency": latency
        }


class SummarizingRAGPipeline(RAGPipeline):
    """RAG pipeline with chunk summarization for large contexts"""
    
    def build_prompt(
        self,
        query: str,
        chunks: List[Dict],
    ) -> str:
        """Build prompt with summarization if needed."""
        system_tokens = len(self.encoding.encode(self.system_prompt))
        query_tokens = len(self.encoding.encode(query))
        reserved_tokens = 2000
        available_tokens = self.max_context_tokens - system_tokens - query_tokens - reserved_tokens
        
        # Try to fit chunks
        context_parts = []
        current_tokens = 0
        
        for chunk in chunks:
            chunk_text = chunk["text"]
            chunk_tokens = len(self.encoding.encode(chunk_text))
            
            if current_tokens + chunk_tokens <= available_tokens:
                context_parts.append(chunk_text)
                current_tokens += chunk_tokens
            else:
                # Summarize this chunk
                summary = summarize_chunk(chunk_text, max_tokens=500)
                summary_tokens = len(self.encoding.encode(summary))
                
                if current_tokens + summary_tokens <= available_tokens:
                    context_parts.append(f"[Summary] {summary}")
                    current_tokens += summary_tokens
        
        context = "\n\n---\n\n".join(context_parts)
        
        prompt = f"""{self.system_prompt}

Context:
{context}

Question: {query}

Answer:"""
        
        return prompt

