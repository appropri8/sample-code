"""Chunk summarization utilities"""

from openai import OpenAI
import os
from typing import Dict, List
from .monitoring import count_tokens


def summarize_chunk(
    text: str,
    max_tokens: int = 500,
    model: str = "gpt-3.5-turbo"
) -> str:
    """
    Summarize a chunk to fit token budget.
    
    Args:
        text: Text to summarize
        max_tokens: Maximum tokens for summary
        model: Model to use for summarization
    
    Returns:
        Summarized text
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""Summarize the following text, preserving key facts and information:

{text}

Concise summary:"""
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3
    )
    
    return response.choices[0].message.content


def summarize_chunks(
    chunks: List[Dict],
    max_total_tokens: int,
    model: str = "gpt-3.5-turbo"
) -> str:
    """
    Summarize multiple chunks to fit within token budget.
    
    Args:
        chunks: List of chunks to summarize
        max_total_tokens: Maximum tokens for combined summary
        model: Model to use for summarization
    
    Returns:
        Combined summarized text
    """
    # Combine chunks
    combined_text = "\n\n---\n\n".join([chunk["text"] for chunk in chunks])
    
    # Summarize
    prompt = f"""Summarize the following text, preserving key information and facts:

{combined_text}

Summary:"""
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_total_tokens,
        temperature=0.3
    )
    
    return response.choices[0].message.content

