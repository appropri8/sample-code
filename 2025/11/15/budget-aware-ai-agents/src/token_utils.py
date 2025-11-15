"""Token estimation utilities."""


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation.
    
    In production, use tiktoken or similar for accuracy.
    Rough estimate: 1 token ≈ 4 characters for English text.
    """
    if not text:
        return 0
    return len(text) // 4


def count_tokens(text: str) -> int:
    """Count tokens in text (alias for estimate_tokens)."""
    return estimate_tokens(text)

