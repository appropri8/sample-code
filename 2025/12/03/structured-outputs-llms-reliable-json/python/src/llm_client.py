"""LLM client wrapper."""
import os
import time
from typing import Optional
from openai import OpenAI


class StructuredLLM:
    """Wrapper for LLM API calls with structured output support."""
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4",
        timeout: int = 30,
        temperature: float = 0.3
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name to use
            timeout: Request timeout in seconds
            temperature: Temperature for generation (lower = more consistent)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY env var)")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
    
    def generate(
        self,
        prompt: str,
        use_json_mode: bool = False,
        functions: list[dict] | None = None
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: Input prompt
            use_json_mode: Whether to use JSON mode (if supported)
            functions: Optional function definitions for function calling
        
        Returns:
            Generated text response
        
        Raises:
            ValueError: If the API call fails
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "timeout": self.timeout
            }
            
            # Use JSON mode if requested and supported
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            # Use function calling if provided
            if functions:
                kwargs["tools"] = [{"type": "function", "function": f} for f in functions]
                if len(functions) == 1:
                    # Force function call if only one function
                    kwargs["tool_choice"] = {"type": "function", "function": {"name": functions[0]["name"]}}
            
            response = self.client.chat.completions.create(**kwargs)
            
            # Handle function calling response
            if response.choices[0].message.tool_calls:
                return response.choices[0].message.tool_calls[0].function.arguments
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise ValueError(f"LLM call failed: {str(e)}") from e
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.model

