"""
Anthropic prompt caching examples.

Demonstrates using Anthropic's explicit prompt caching feature.
Requires ANTHROPIC_API_KEY environment variable.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if anthropic is available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. Install with: pip install anthropic")


class AnthropicCacheExample:
    """Examples of using Anthropic's prompt caching."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with API key.
        
        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package required")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def basic_caching_example(self):
        """
        Basic example: Cache a system prompt.
        """
        print("=== Basic Caching Example ===\n")
        
        system_prompt = """You are a helpful customer support assistant for TechCorp.
        
Guidelines:
- Be professional and friendly
- Check our knowledge base before answering
- Escalate complex issues to human agents
- Never make promises about product timelines
- Always cite sources when providing information

Our products:
- TechCorp Pro: $99/month, includes 24/7 support
- TechCorp Business: $299/month, includes dedicated account manager
- TechCorp Enterprise: Custom pricing, includes white-glove service

Common policies:
- Refunds available within 60 days
- Cancellation requires 30 days notice
- Data export available on all plans"""
        
        # First request - will cache the system prompt
        print("First request (cache miss):")
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": "What are your refund terms?"}
            ]
        )
        
        print(f"Response: {response.content[0].text[:100]}...")
        print(f"Usage: {response.usage}")
        print()
        
        # Second request - should hit cache
        print("Second request (cache hit):")
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": "What pricing plans do you offer?"}
            ]
        )
        
        print(f"Response: {response.content[0].text[:100]}...")
        print(f"Usage: {response.usage}")
        print()
    
    def multi_turn_conversation_example(self):
        """
        Example: Cache conversation history in multi-turn chat.
        """
        print("=== Multi-Turn Conversation Example ===\n")
        
        system_prompt = "You are a helpful assistant. Be concise."
        
        # Turn 1
        print("Turn 1:")
        messages_1 = [
            {"role": "user", "content": "What is Python?"}
        ]
        
        response_1 = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=messages_1
        )
        
        print(f"User: {messages_1[0]['content']}")
        print(f"Assistant: {response_1.content[0].text[:100]}...")
        print()
        
        # Turn 2 - cache previous conversation
        print("Turn 2 (caching previous turns):")
        messages_2 = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": response_1.content[0].text},
            {
                "role": "user",
                "content": "What is it used for?",
                "cache_control": {"type": "ephemeral"}  # Cache up to here
            }
        ]
        
        response_2 = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=messages_2
        )
        
        print(f"User: {messages_2[-1]['content']}")
        print(f"Assistant: {response_2.content[0].text[:100]}...")
        print(f"Usage: {response_2.usage}")
        print()
    
    def large_context_example(self):
        """
        Example: Cache large context document.
        """
        print("=== Large Context Example ===\n")
        
        # Simulate a large document
        large_document = """
        [Large 10,000-token technical documentation that rarely changes]
        
        This is a simulation of a large context document that would be
        expensive to process repeatedly. In a real application, this would
        be your actual documentation, policy manual, codebase, etc.
        
        """ * 100  # Repeat to simulate large document
        
        print(f"Document size: ~{len(large_document.split())} words")
        print()
        
        # First request with large context
        print("First request (cache miss):")
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": f"You are a helpful assistant. Use this context:\n\n{large_document}",
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": "Summarize the key points"}
            ]
        )
        
        print(f"Response: {response.content[0].text[:100]}...")
        print(f"Usage: {response.usage}")
        print()
        
        # Second request - should reuse cached context
        print("Second request (cache hit):")
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": f"You are a helpful assistant. Use this context:\n\n{large_document}",
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": "What are the main topics?"}
            ]
        )
        
        print(f"Response: {response.content[0].text[:100]}...")
        print(f"Usage: {response.usage}")
        print()


def demo_anthropic_caching():
    """Run Anthropic caching demos."""
    if not ANTHROPIC_AVAILABLE:
        print("Anthropic package not installed.")
        print("Install with: pip install anthropic")
        return
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment.")
        print("Set it with: export ANTHROPIC_API_KEY=your_key")
        return
    
    try:
        examples = AnthropicCacheExample(api_key)
        
        examples.basic_caching_example()
        # Uncomment to run more examples:
        # examples.multi_turn_conversation_example()
        # examples.large_context_example()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    demo_anthropic_caching()
