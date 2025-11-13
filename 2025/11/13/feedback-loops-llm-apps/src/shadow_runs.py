"""Shadow run utilities for testing new versions safely"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime


async def shadow_run(
    input_text: str,
    prompt_v1: str,
    prompt_v2: str,
    model: str = "gpt-4",
    call_llm_func=None
) -> Dict[str, Any]:
    """
    Run both versions, log both, but only return v1.
    
    Args:
        input_text: User input
        prompt_v1: Production prompt
        prompt_v2: Shadow prompt to test
        model: Model to use
        call_llm_func: Function to call LLM (async)
    
    Returns:
        Result from v1 (production)
    """
    if call_llm_func is None:
        # Default implementation
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        
        async def default_call_llm(text: str, prompt: str):
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ]
            )
            return {
                "output": response.choices[0].message.content,
                "tokens": {
                    "input": response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens
                }
            }
        
        call_llm_func = default_call_llm
    
    # Run production version (wait for it)
    result_v1 = await call_llm_func(input_text, prompt_v1)
    
    # Run shadow version (don't wait, run in background)
    shadow_task = asyncio.create_task(call_llm_func(input_text, prompt_v2))
    
    # Log shadow comparison (after shadow completes)
    async def log_comparison():
        try:
            result_v2 = await shadow_task
            log_shadow_comparison(
                input_text=input_text,
                result_v1=result_v1,
                result_v2=result_v2,
                prompt_v1=prompt_v1,
                prompt_v2=prompt_v2
            )
        except Exception as e:
            print(f"Error in shadow run: {e}")
    
    # Don't wait for shadow to complete
    asyncio.create_task(log_comparison())
    
    # Return only v1 to user
    return result_v1


def log_shadow_comparison(
    input_text: str,
    result_v1: Dict[str, Any],
    result_v2: Dict[str, Any],
    prompt_v1: str,
    prompt_v2: str
):
    """Log shadow run comparison."""
    from src.feedback import insert_feedback
    import hashlib
    
    request_id = f"shadow_{int(datetime.utcnow().timestamp() * 1000)}"
    
    # Log v1
    insert_feedback(
        conversation_id=f"shadow_{request_id}",
        turn_id=1,
        request_id=f"{request_id}_v1",
        input_text=input_text,
        output_text=result_v1.get("output", ""),
        prompt_version="v1_shadow",
        model="gpt-4",
        metadata={
            "shadow_run": True,
            "tokens": result_v1.get("tokens", {}),
            "prompt": prompt_v1[:100]  # First 100 chars
        }
    )
    
    # Log v2
    insert_feedback(
        conversation_id=f"shadow_{request_id}",
        turn_id=2,
        request_id=f"{request_id}_v2",
        input_text=input_text,
        output_text=result_v2.get("output", ""),
        prompt_version="v2_shadow",
        model="gpt-4",
        metadata={
            "shadow_run": True,
            "tokens": result_v2.get("tokens", {}),
            "prompt": prompt_v2[:100]  # First 100 chars
        }
    )


async def batch_shadow_run(
    inputs: list,
    prompt_v1: str,
    prompt_v2: str,
    model: str = "gpt-4",
    call_llm_func=None
) -> Dict[str, Any]:
    """
    Run shadow comparison on multiple inputs.
    Useful for testing on historical data.
    """
    results = []
    
    for input_text in inputs:
        result = await shadow_run(
            input_text=input_text,
            prompt_v1=prompt_v1,
            prompt_v2=prompt_v2,
            model=model,
            call_llm_func=call_llm_func
        )
        results.append(result)
        
        # Small delay to avoid rate limits
        await asyncio.sleep(0.1)
    
    return {
        "total": len(results),
        "results": results
    }

