"""Retry strategy examples."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.schema import TaskTriage
from src.prompt_builder import build_structured_prompt, add_error_feedback
from src.llm_client import StructuredLLM
from src.structured_output import get_structured_output


def main():
    """Demonstrate retry strategies."""
    print("Retry Strategy Examples\n" + "=" * 50)
    
    # Initialize LLM client
    llm = StructuredLLM(
        model="gpt-4",
        temperature=0.3
    )
    
    issue = "User cannot log in after password reset"
    
    # Build initial prompt
    prompt = build_structured_prompt(
        schema=TaskTriage,
        input_text=issue,
        task_description="Categorize and prioritize the following issue."
    )
    
    print(f"Issue: {issue}")
    print(f"Max retries: 3")
    print("-" * 50)
    
    try:
        result = get_structured_output(
            llm=llm,
            prompt=prompt,
            schema=TaskTriage,
            max_retries=3,
            enable_repair=True
        )
        
        print(f"\n✓ Success after retries:")
        print(f"Category: {result.category.value}")
        print(f"Priority: {result.priority}")
        print(f"Needs Human: {result.needs_human}")
        
    except Exception as e:
        print(f"\n✗ Failed after all retries: {e}")


if __name__ == "__main__":
    main()

