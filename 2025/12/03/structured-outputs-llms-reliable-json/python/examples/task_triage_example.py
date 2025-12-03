"""Complete task triage API example."""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.schema import TaskTriage, Category
from src.prompt_builder import build_structured_prompt
from src.llm_client import StructuredLLM
from src.structured_output import get_structured_output

load_dotenv()


def main():
    """Run task triage example."""
    # Initialize LLM client
    llm = StructuredLLM(
        model="gpt-4",
        temperature=0.3
    )
    
    # Example issue descriptions
    issues = [
        "User reported that they cannot log in after resetting their password. This is blocking them from accessing their account.",
        "Feature request: Add dark mode to the mobile app",
        "Question: How do I export my data?",
        "The payment processing is broken and customers can't complete purchases. This is urgent."
    ]
    
    print("Task Triage Example\n" + "=" * 50)
    
    for issue in issues:
        print(f"\nIssue: {issue}")
        print("-" * 50)
        
        # Build prompt
        prompt = build_structured_prompt(
            schema=TaskTriage,
            input_text=issue,
            task_description="Categorize and prioritize the following issue.",
            examples=[
                {
                    "category": "bug",
                    "priority": 3,
                    "needs_human": True,
                    "summary": "User cannot log in after password reset"
                }
            ]
        )
        
        try:
            # Get structured output
            result = get_structured_output(
                llm=llm,
                prompt=prompt,
                schema=TaskTriage,
                max_retries=3
            )
            
            print(f"Category: {result.category.value}")
            print(f"Priority: {result.priority}")
            print(f"Needs Human: {result.needs_human}")
            if result.summary:
                print(f"Summary: {result.summary}")
            
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()

