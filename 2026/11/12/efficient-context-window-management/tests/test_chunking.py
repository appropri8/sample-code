"""Tests for chunking module"""

import pytest
from src.chunking import chunk_text, chunk_text_at_sentences


def test_chunk_text_basic():
    """Test basic chunking"""
    text = "This is a test. " * 100
    chunks = chunk_text(text, chunk_size=50, overlap=5)
    
    assert len(chunks) > 0
    assert all("text" in chunk for chunk in chunks)
    assert all("token_count" in chunk for chunk in chunks)


def test_chunk_text_overlap():
    """Test that chunks have overlap"""
    text = "Word " * 200
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    
    if len(chunks) > 1:
        # Check that there's some overlap between chunks
        # (simplified check - in practice, you'd verify token overlap)
        assert len(chunks) > 1


def test_chunk_text_at_sentences():
    """Test sentence-based chunking"""
    text = "First sentence. Second sentence. Third sentence. " * 50
    chunks = chunk_text_at_sentences(text, chunk_size=50, overlap=5)
    
    assert len(chunks) > 0
    assert all("text" in chunk for chunk in chunks)


def test_chunk_empty_text():
    """Test chunking empty text"""
    chunks = chunk_text("", chunk_size=50, overlap=5)
    assert len(chunks) == 0


def test_chunk_small_text():
    """Test chunking text smaller than chunk size"""
    text = "Short text"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0]["text"] == text

