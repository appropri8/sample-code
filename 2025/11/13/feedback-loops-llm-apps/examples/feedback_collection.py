"""Example: Collecting different types of feedback"""

from src.feedback import (
    insert_feedback,
    collect_explicit_feedback,
    collect_implicit_feedback,
    collect_outcome_feedback
)


def example_explicit_feedback():
    """Example: Collect explicit feedback from users."""
    request_id = "req_12345"
    
    # User gives thumbs up
    collect_explicit_feedback(
        request_id=request_id,
        thumbs_up=True
    )
    
    # User gives rating and comment
    collect_explicit_feedback(
        request_id=request_id,
        rating=5,
        comment="Great answer! Very helpful."
    )


def example_implicit_feedback():
    """Example: Collect implicit feedback from user actions."""
    request_id = "req_12345"
    
    # User edited 80% of the output
    collect_implicit_feedback(
        request_id=request_id,
        edit_ratio=0.8
    )
    
    # User abandoned the flow
    collect_implicit_feedback(
        request_id=request_id,
        abandoned=True
    )
    
    # User took a long time to complete
    collect_implicit_feedback(
        request_id=request_id,
        time_to_completion=300.0  # 5 minutes
    )


def example_outcome_feedback():
    """Example: Collect outcome-based feedback."""
    request_id = "req_12345"
    
    # Task succeeded
    collect_outcome_feedback(
        request_id=request_id,
        task_succeeded=True
    )
    
    # Needed human help
    collect_outcome_feedback(
        request_id=request_id,
        needed_human_help=False
    )
    
    # Safety filter triggered
    collect_outcome_feedback(
        request_id=request_id,
        safety_filter_level="medium"
    )


def example_complete_feedback_flow():
    """Example: Complete feedback flow from request to outcome."""
    request_id = "req_67890"
    conversation_id = "conv_123"
    
    # 1. Log initial request/response
    insert_feedback(
        conversation_id=conversation_id,
        turn_id=1,
        request_id=request_id,
        input_text="How do I handle errors in Python?",
        output_text="Use try-except blocks to handle errors...",
        prompt_version="v1",
        model="gpt-4"
    )
    
    # 2. User gives explicit feedback
    collect_explicit_feedback(
        request_id=request_id,
        rating=4,
        comment="Good answer, but could be more detailed"
    )
    
    # 3. User edits the output (implicit feedback)
    collect_implicit_feedback(
        request_id=request_id,
        edit_ratio=0.3  # User edited 30% of the output
    )
    
    # 4. Task outcome (outcome-based feedback)
    collect_outcome_feedback(
        request_id=request_id,
        task_succeeded=True,
        needed_human_help=False
    )


if __name__ == "__main__":
    print("Example: Explicit feedback")
    example_explicit_feedback()
    
    print("\nExample: Implicit feedback")
    example_implicit_feedback()
    
    print("\nExample: Outcome feedback")
    example_outcome_feedback()
    
    print("\nExample: Complete feedback flow")
    example_complete_feedback_flow()
    
    print("\nAll examples completed!")

