"""
Example 5: FastAPI Integration

Production-ready REST endpoint with:
- Schema validation
- Error handling
- Metrics tracking
- Response formatting
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Literal
import time
from datetime import datetime

# Import our modules
import sys
sys.path.insert(0, '.')

app = FastAPI(
    title="Deterministic AI Extraction API",
    description="Schema-constrained LLM extraction with validation",
    version="1.0.0"
)


# Request/Response schemas
class ExtractionRequest(BaseModel):
    """Request to extract structured information"""
    text: str = Field(
        description="Text to extract information from",
        min_length=10,
        max_length=5000
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts"
    )


class TaskResult(BaseModel):
    """Extracted task information"""
    title: str
    priority: Literal[1, 2, 3, 4, 5]
    category: Literal["bug", "feature", "docs", "refactor"]
    description: str | None = None
    tags: list[str] = []


class ExtractionResponse(BaseModel):
    """Response from extraction endpoint"""
    success: bool
    data: TaskResult | None = None
    metadata: dict
    errors: list[str] = []


# Task extraction schema
class TaskExtraction(BaseModel):
    """Extract task information from text"""
    version: Literal["2.0"] = "2.0"
    title: str = Field(min_length=5, max_length=100)
    priority: Literal[1, 2, 3, 4, 5]
    category: Literal["bug", "feature", "docs", "refactor"]
    description: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=5)


def mock_llm_call(prompt: str) -> str:
    """Mock LLM call for demonstration"""
    # Simulate API latency
    time.sleep(0.1)
    
    # Return a valid response
    return """{
        "version": "2.0",
        "title": "Fix critical authentication bug",
        "priority": 4,
        "category": "bug",
        "description": "Users cannot log in after recent update",
        "tags": ["auth", "urgent"]
    }"""


@app.post("/extract", response_model=ExtractionResponse)
async def extract_task(request: ExtractionRequest):
    """
    Extract structured task information from text
    
    Returns validated task data with metadata about the extraction process.
    """
    from src.validation_middleware import ValidationMiddleware
    from src.retry_logic import RetryStrategy, RetryConfig
    
    start_time = time.time()
    
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "input_length": len(request.text),
        "schema_version": "2.0",
        "attempts": 0,
        "latency_ms": 0
    }
    
    try:
        # Build prompt
        import json
        schema_json = TaskExtraction.model_json_schema()
        prompt = f"""Extract task information from this text:

{request.text}

Return valid JSON matching this schema:
{json.dumps(schema_json, indent=2)}"""
        
        # Try extraction with retries
        config = RetryConfig(max_retries=request.max_retries)
        result, retries, error_log = RetryStrategy.retry_with_validation(
            mock_llm_call,
            prompt,
            TaskExtraction,
            config
        )
        
        metadata["attempts"] = retries + 1
        metadata["latency_ms"] = (time.time() - start_time) * 1000
        
        if result is not None:
            # Success
            return ExtractionResponse(
                success=True,
                data=TaskResult(**result.model_dump()),
                metadata=metadata,
                errors=[]
            )
        else:
            # Failed after retries
            return ExtractionResponse(
                success=False,
                data=None,
                metadata=metadata,
                errors=error_log
            )
    
    except Exception as e:
        # Unexpected error
        metadata["latency_ms"] = (time.time() - start_time) * 1000
        
        return ExtractionResponse(
            success=False,
            data=None,
            metadata=metadata,
            errors=[f"Internal error: {str(e)}"]
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/schema")
async def get_schema():
    """Get the JSON schema for task extraction"""
    return TaskExtraction.model_json_schema()


# Example usage for testing
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Example 5: FastAPI Integration")
    print("=" * 60)
    print("\nStarting FastAPI server...")
    print("Visit http://localhost:8000/docs for interactive API documentation")
    print("\nExample curl command:")
    print('curl -X POST http://localhost:8000/extract \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"text": "High priority: Fix login bug in auth service"}\'')
    print("\n" + "=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
