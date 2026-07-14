"""
Example 2: JSON Schema Generation

Demonstrates converting Pydantic models to JSON Schema for LLM consumption.
Shows how to generate schemas that models can understand and follow.
"""

import json
from pydantic import BaseModel, Field
from typing import Literal


class TaskExtraction(BaseModel):
    """Extract task information from text"""
    
    title: str = Field(
        description="Task title, should be clear and concise",
        min_length=5,
        max_length=100
    )
    priority: Literal[1, 2, 3, 4, 5] = Field(
        description="Priority level where 1 is lowest and 5 is highest"
    )
    category: Literal["bug", "feature", "docs", "refactor"] = Field(
        description="Type of task"
    )
    description: str | None = Field(
        None,
        description="Optional detailed description of the task"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Up to 5 relevant tags",
        max_length=5
    )


def generate_json_schema(schema: type[BaseModel]) -> dict:
    """Generate JSON Schema from Pydantic model"""
    return schema.model_json_schema()


def build_llm_prompt_with_schema(schema: type[BaseModel], user_input: str) -> str:
    """Build a prompt that includes the JSON Schema"""
    
    schema_json = generate_json_schema(schema)
    
    prompt = f"""Extract structured information from the following text.

Return valid JSON that matches this schema:
{json.dumps(schema_json, indent=2)}

Text to extract from:
{user_input}

Return only valid JSON, no other text."""
    
    return prompt


def demonstrate_json_schema():
    """Demonstrate JSON Schema generation"""
    
    print("=" * 60)
    print("Example 2: JSON Schema Generation")
    print("=" * 60)
    
    # Generate full JSON Schema
    print("\n1. Full JSON Schema:")
    schema = generate_json_schema(TaskExtraction)
    print(json.dumps(schema, indent=2))
    
    # Show required fields
    print("\n2. Required Fields:")
    required_fields = schema.get("required", [])
    print(f"   {required_fields}")
    
    # Show field types
    print("\n3. Field Types:")
    properties = schema.get("properties", {})
    for field_name, field_info in properties.items():
        field_type = field_info.get("type", "unknown")
        if "anyOf" in field_info:
            types = [t.get("type") for t in field_info["anyOf"] if "type" in t]
            field_type = f"{' | '.join(types)}"
        print(f"   {field_name}: {field_type}")
    
    # Show enum constraints
    print("\n4. Enum Constraints:")
    for field_name, field_info in properties.items():
        if "enum" in field_info:
            print(f"   {field_name}: {field_info['enum']}")
        elif "anyOf" in field_info:
            for subtype in field_info["anyOf"]:
                if "enum" in subtype:
                    print(f"   {field_name}: {subtype['enum']}")
    
    # Show a complete LLM prompt with schema
    print("\n5. LLM Prompt with Schema:")
    user_input = "We need to fix the critical authentication bug ASAP"
    prompt = build_llm_prompt_with_schema(TaskExtraction, user_input)
    print(prompt)
    
    # Simplified schema for LLM (only essential info)
    print("\n6. Simplified Schema (for token efficiency):")
    simplified = {
        "type": "object",
        "required": required_fields,
        "properties": {
            name: {
                "type": info.get("type"),
                "enum": info.get("enum"),
                "description": info.get("description")
            }
            for name, info in properties.items()
        }
    }
    print(json.dumps(simplified, indent=2))
    
    print("\n" + "=" * 60)
    print("JSON Schema generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_json_schema()
