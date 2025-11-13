"""LLM client with schema validation and retry logic."""

import json
import logging
from typing import TypeVar, Type, Optional
from pydantic import BaseModel, ValidationError
from openai import OpenAI

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """Client for calling LLMs with schema validation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """Initialize LLM client.
        
        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            model: Model name to use.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def call_with_schema(
        self,
        prompt: str,
        schema_class: Type[T],
        system_prompt: Optional[str] = None,
        max_retries: int = 3
    ) -> T:
        """Call LLM and validate response against schema, with retry on failure.
        
        Args:
            prompt: User prompt
            schema_class: Pydantic model class to validate against
            system_prompt: Optional system prompt
            max_retries: Maximum number of retries on validation failure
            
        Returns:
            Validated instance of schema_class
            
        Raises:
            ValueError: If validation fails after max_retries
        """
        default_system = (
            f"Return valid JSON matching this schema: {schema_class.model_json_schema()}. "
            "Do not include any text outside the JSON."
        )
        system = system_prompt or default_system
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                # Parse JSON
                raw_output = response.choices[0].message.content
                parsed = json.loads(raw_output)
                
                # Validate against schema
                return schema_class(**parsed)
                
            except json.JSONDecodeError as e:
                if attempt == max_retries - 1:
                    raise ValueError(
                        f"Failed to parse JSON after {max_retries} attempts: {e}"
                    )
                
                # Retry with error feedback
                error_feedback = (
                    f"Previous response was not valid JSON: {str(e)}. "
                    "Please return valid JSON matching the schema."
                )
                prompt = f"{prompt}\n\nError: {error_feedback}"
                logger.warning(f"JSON parse error on attempt {attempt + 1}, retrying...")
                
            except ValidationError as e:
                if attempt == max_retries - 1:
                    raise ValueError(
                        f"Failed to validate response after {max_retries} attempts: {e}"
                    )
                
                # Retry with error feedback
                error_feedback = (
                    f"Previous response did not match schema: {str(e)}. "
                    "Please return valid JSON matching the schema exactly."
                )
                prompt = f"{prompt}\n\nError: {error_feedback}"
                logger.warning(f"Validation error on attempt {attempt + 1}, retrying...")
        
        raise ValueError("Unexpected error in retry loop")
    
    def call_with_tools(
        self,
        prompt: str,
        tools: list,
        system_prompt: Optional[str] = None
    ) -> dict:
        """Call LLM with tool definitions.
        
        Args:
            prompt: User prompt
            tools: List of tool definitions
            system_prompt: Optional system prompt
            
        Returns:
            Response with potential tool calls
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools
        )
        
        return {
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls
        }

