"""Build prompts from schemas."""
import json
from typing import Type
from pydantic import BaseModel


def build_structured_prompt(
    schema: Type[BaseModel],
    input_text: str,
    examples: list[dict] | None = None,
    task_description: str | None = None
) -> str:
    """
    Build a prompt that asks for structured JSON output.
    
    Args:
        schema: Pydantic model class
        input_text: Input text to process
        examples: Optional list of example outputs
        task_description: Optional custom task description
    
    Returns:
        Formatted prompt string
    """
    schema_json = schema.model_json_schema()
    
    # Build examples text
    examples_text = ""
    if examples:
        examples_text = "\n\nExamples:\n"
        for ex in examples:
            examples_text += json.dumps(ex, indent=2) + "\n"
    
    # Default task description
    if task_description is None:
        task_description = f"Extract information from the text and return it as JSON."
    
    prompt = f"""You are a JSON API. {task_description}

Text to process:
{input_text}

Required JSON schema:
{json.dumps(schema_json, indent=2)}
{examples_text}
Rules:
1. Return ONLY the JSON object, no other text
2. Do not include markdown code blocks (```json or ```)
3. Do not include explanations or comments
4. Use double quotes for all strings
5. No trailing commas
6. Escape special characters in strings (\\n, \\", \\\\)
7. All required fields must be present
8. Do not add fields that are not in the schema

Return the JSON now:"""
    
    return prompt


def add_error_feedback(
    original_prompt: str,
    error_message: str,
    raw_response: str | None = None
) -> str:
    """
    Add error feedback to a prompt for retry.
    
    Args:
        original_prompt: Original prompt
        error_message: Error message from previous attempt
        raw_response: Optional raw response from previous attempt
    
    Returns:
        Updated prompt with error feedback
    """
    feedback = f"""

Previous attempt failed with error: {error_message}"""
    
    if raw_response:
        # Truncate long responses
        truncated = raw_response[:200] + "..." if len(raw_response) > 200 else raw_response
        feedback += f"\nResponse received: {truncated}"
    
    feedback += "\n\nPlease fix the issue and return valid JSON matching the schema."
    
    return original_prompt + feedback

