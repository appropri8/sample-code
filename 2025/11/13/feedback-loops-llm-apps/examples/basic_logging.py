"""Example: Basic logging with FastAPI middleware"""

from fastapi import FastAPI, Request
from src.logging_middleware import LLMLoggingMiddleware
from openai import OpenAI
import os

app = FastAPI()

# Add logging middleware
app.add_middleware(LLMLoggingMiddleware)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/api/llm")
async def llm_endpoint(request: dict):
    """LLM endpoint with automatic logging."""
    input_text = request.get("input", "")
    prompt_version = request.get("prompt_version", "v1")
    model = request.get("model", "gpt-4")
    
    # Get prompt based on version
    prompt = get_prompt(prompt_version)
    
    # Call LLM
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_text}
        ]
    )
    
    output = response.choices[0].message.content
    
    return {
        "output": output,
        "tokens": {
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens
        },
        "cost_estimate": estimate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            model
        )
    }


def get_prompt(version: str) -> str:
    """Get prompt by version."""
    prompts = {
        "v1": "You are a helpful assistant.",
        "v2": "You are a helpful assistant. Always be concise."
    }
    return prompts.get(version, prompts["v1"])


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Estimate cost."""
    pricing = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002}
    }
    
    if model not in pricing:
        model = "gpt-4"
    
    return (
        (prompt_tokens / 1000) * pricing[model]["prompt"] +
        (completion_tokens / 1000) * pricing[model]["completion"]
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

