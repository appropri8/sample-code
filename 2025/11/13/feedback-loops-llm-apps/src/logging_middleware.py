"""Logging middleware for FastAPI to log LLM requests"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def sanitize_input(text: str) -> str:
    """Remove PII and sensitive data from input text."""
    # In production, use proper PII detection libraries
    # This is a simplified example
    # Remove email patterns
    import re
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    # Remove phone patterns
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', text)
    return text


def hash_user_id(user_id: str) -> str:
    """Hash user ID for privacy."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


class LLMLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log LLM requests and responses."""
    
    def __init__(self, app, log_callback=None):
        super().__init__(app)
        self.log_callback = log_callback or self._default_log
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log LLM interactions."""
        if "/api/llm" not in str(request.url):
            return await call_next(request)
        
        start_time = time.time()
        request_id = f"req_{int(time.time() * 1000)}"
        
        # Read request body
        body = await request.body()
        
        # Log request
        try:
            data = json.loads(body)
            user_input = sanitize_input(data.get("input", ""))
            prompt_version = data.get("prompt_version", "v1")
            model = data.get("model", "gpt-4")
            
            log_entry = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id_hash": hash_user_id(data.get("user_id", "anonymous")),
                "input": user_input,
                "prompt_version": prompt_version,
                "model": model,
                "tools": data.get("tools", [])
            }
            
            self.log_callback("request", log_entry)
            
        except Exception as e:
            self.log_callback("error", {"error": str(e), "request_id": request_id})
        
        # Process request
        response = await call_next(request)
        
        # Log response
        elapsed = time.time() - start_time
        
        # Read response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        try:
            response_data = json.loads(response_body)
            response_log = {
                "request_id": request_id,
                "output": response_data.get("output", ""),
                "tokens_input": response_data.get("tokens", {}).get("input", 0),
                "tokens_output": response_data.get("tokens", {}).get("output", 0),
                "latency_ms": elapsed * 1000,
                "cost_estimate": response_data.get("cost_estimate", 0)
            }
            self.log_callback("response", response_log)
        except Exception as e:
            self.log_callback("error", {"error": str(e), "request_id": request_id})
        
        # Recreate response with body
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
    
    def _default_log(self, log_type: str, data: Dict[str, Any]):
        """Default logging function (prints to console)."""
        print(f"LOG [{log_type}]: {json.dumps(data)}")

