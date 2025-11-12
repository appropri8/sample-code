"""Document chunking utilities"""

from typing import List, Dict, Any
import tiktoken


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    encoding_name: str = "cl100k_base"
) -> List[Dict[str, Any]]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in tokens
        overlap: Overlap size in tokens
        encoding_name: Tokenizer encoding
    
    Returns:
        List of chunks with metadata
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        
        chunks.append({
            "text": chunk_text,
            "start_token": start,
            "end_token": end,
            "token_count": len(chunk_tokens)
        })
        
        # Move start forward, accounting for overlap
        start = end - overlap
    
    return chunks


def chunk_text_at_sentences(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    encoding_name: str = "cl100k_base"
) -> List[Dict[str, Any]]:
    """
    Split text into chunks at sentence boundaries.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in tokens
        overlap: Overlap size in tokens
        encoding_name: Tokenizer encoding
    
    Returns:
        List of chunks with metadata
    """
    import re
    
    # Split into sentences (simple approach)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    encoding = tiktoken.get_encoding(encoding_name)
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sentence in sentences:
        sentence_tokens = len(encoding.encode(sentence))
        
        if current_tokens + sentence_tokens > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "token_count": current_tokens
            })
            
            # Start new chunk with overlap
            overlap_sentences = []
            overlap_tokens = 0
            for s in reversed(current_chunk):
                s_tokens = len(encoding.encode(s))
                if overlap_tokens + s_tokens <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_tokens += s_tokens
                else:
                    break
            
            current_chunk = overlap_sentences + [sentence]
            current_tokens = overlap_tokens + sentence_tokens
        else:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
    
    # Add final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({
            "text": chunk_text,
            "token_count": current_tokens
        })
    
    return chunks

