"""
Prompt normalization utilities.

Demonstrates techniques to normalize prompts for better cache hits:
1. Whitespace normalization
2. JSON key sorting
3. Stable list ordering
"""

import json
import re
from typing import Any, Dict, List


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    - Replace multiple spaces with single space
    - Remove leading/trailing whitespace
    - Normalize line endings
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_json(data: Any, sort_keys: bool = True) -> str:
    """
    Normalize JSON for consistent formatting.
    
    Args:
        data: Data to serialize
        sort_keys: Whether to sort dictionary keys
        
    Returns:
        Normalized JSON string
    """
    return json.dumps(data, sort_keys=sort_keys, separators=(',', ':'))


def normalize_list(items: List[str], sort: bool = True) -> str:
    """
    Normalize list to stable string representation.
    
    Args:
        items: List of strings
        sort: Whether to sort the list
        
    Returns:
        Comma-separated string
    """
    if sort:
        items = sorted(items)
    return ", ".join(items)


def normalize_prompt(prompt: str) -> str:
    """
    Apply all normalization to a prompt.
    
    Args:
        prompt: Raw prompt
        
    Returns:
        Normalized prompt
    """
    # Normalize whitespace
    normalized = normalize_whitespace(prompt)
    
    # Could add more normalization here
    # - Lowercase for case-insensitive matching
    # - Remove punctuation
    # etc.
    
    return normalized


def extract_and_normalize_json(text: str) -> str:
    """
    Find JSON in text and normalize it.
    
    Useful when prompts contain JSON data that should be normalized.
    
    Args:
        text: Text potentially containing JSON
        
    Returns:
        Text with normalized JSON
    """
    # Find JSON patterns (basic implementation)
    import re
    
    def replace_json(match):
        try:
            json_str = match.group(0)
            data = json.loads(json_str)
            return normalize_json(data)
        except:
            return match.group(0)
    
    # Match JSON objects and arrays
    pattern = r'\{[^{}]*\}|\[[^\[\]]*\]'
    return re.sub(pattern, replace_json, text)


def demo_normalization():
    """Demonstrate normalization techniques."""
    print("=== Prompt Normalization Demo ===\n")
    
    # 1. Whitespace normalization
    print("1. Whitespace Normalization")
    messy_prompt = """You are a helpful    assistant.


Question: What  is   Python?"""
    
    normalized = normalize_whitespace(messy_prompt)
    print(f"Original: {repr(messy_prompt)}")
    print(f"Normalized: {repr(normalized)}")
    print()
    
    # 2. JSON normalization
    print("2. JSON Normalization")
    data = {"user": "alice", "question": "What is Python?", "id": 123}
    
    # Different orderings should produce same result
    data1 = {"id": 123, "user": "alice", "question": "What is Python?"}
    data2 = {"question": "What is Python?", "id": 123, "user": "alice"}
    
    print(f"Data 1: {json.dumps(data1)}")
    print(f"Data 2: {json.dumps(data2)}")
    print(f"Normalized 1: {normalize_json(data1)}")
    print(f"Normalized 2: {normalize_json(data2)}")
    print(f"Match: {normalize_json(data1) == normalize_json(data2)}")
    print()
    
    # 3. List normalization
    print("3. List Normalization")
    list1 = ["Python", "JavaScript", "Go"]
    list2 = ["Go", "Python", "JavaScript"]
    
    print(f"List 1: {list1}")
    print(f"List 2: {list2}")
    print(f"Normalized 1: {normalize_list(list1)}")
    print(f"Normalized 2: {normalize_list(list2)}")
    print(f"Match: {normalize_list(list1) == normalize_list(list2)}")
    print()
    
    # 4. Complete prompt normalization
    print("4. Complete Prompt Normalization")
    
    prompts = [
        "You are a helpful assistant.\n\nQuestion: What is Python?",
        "You are a helpful assistant.\n\n\nQuestion: What is Python?",
        "You are a helpful   assistant.\n\nQuestion:  What is Python?",
    ]
    
    print("Original prompts (different):")
    for i, p in enumerate(prompts, 1):
        print(f"  {i}: {repr(p)}")
    
    print("\nNormalized prompts (same):")
    normalized_prompts = [normalize_prompt(p) for p in prompts]
    for i, p in enumerate(normalized_prompts, 1):
        print(f"  {i}: {repr(p)}")
    
    print(f"\nAll match: {len(set(normalized_prompts)) == 1}")


class PromptBuilder:
    """Build prompts with automatic normalization."""
    
    def __init__(self, system_prompt: str):
        """
        Initialize with system prompt.
        
        Args:
            system_prompt: Static system prompt
        """
        self.system_prompt = normalize_whitespace(system_prompt)
    
    def build(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """
        Build normalized prompt.
        
        Args:
            user_query: User's question
            context: Optional context dictionary
            
        Returns:
            Normalized prompt
        """
        parts = [self.system_prompt]
        
        if context:
            # Normalize context JSON
            context_str = f"Context: {normalize_json(context)}"
            parts.append(context_str)
        
        # User query at the end
        parts.append(f"Question: {normalize_whitespace(user_query)}")
        
        return "\n\n".join(parts)


def demo_prompt_builder():
    """Demonstrate prompt builder."""
    print("\n=== Prompt Builder Demo ===\n")
    
    builder = PromptBuilder("You are a helpful assistant.")
    
    # Same query, different formatting - should produce same prompt
    queries = [
        "What is Python?",
        "What  is  Python?",
        "What is Python? ",
    ]
    
    print("Building prompts with different formatting:")
    for i, query in enumerate(queries, 1):
        prompt = builder.build(query)
        print(f"\nQuery {i}: {repr(query)}")
        print(f"Prompt hash: {hash(prompt)}")
    
    # With context
    context1 = {"user_id": 123, "session": "abc"}
    context2 = {"session": "abc", "user_id": 123}  # Different order
    
    print("\n\nWith context (different order, same result):")
    prompt1 = builder.build("What is Python?", context1)
    prompt2 = builder.build("What is Python?", context2)
    
    print(f"Prompt 1 hash: {hash(prompt1)}")
    print(f"Prompt 2 hash: {hash(prompt2)}")
    print(f"Match: {prompt1 == prompt2}")


if __name__ == "__main__":
    demo_normalization()
    demo_prompt_builder()
