"""Instrumented LLM wrapper with observability"""

import time
import uuid
from typing import Dict, Any
from openai import OpenAI
from .logger import ObservabilityLogger


class InstrumentedLLM:
    """LLM wrapper that automatically logs all calls"""
    
    def __init__(self, logger: ObservabilityLogger, api_key: str = None):
        self.logger = logger
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
    
    def call(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        prompt_version: str = "v1",
        **kwargs
    ) -> Dict[str, Any]:
        """Make an LLM call with automatic logging"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            self.logger.log_llm_call(
                request_id=request_id,
                prompt_version=prompt_version,
                model=model,
                prompt=prompt,
                response=content,
                usage=usage,
                latency_ms=latency_ms,
                status="success"
            )
            
            return {
                "content": content,
                "request_id": request_id,
                "usage": usage,
                "latency_ms": latency_ms
            }
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.logger.log_llm_call(
                request_id=request_id,
                prompt_version=prompt_version,
                model=model,
                prompt=prompt,
                response="",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency_ms=latency_ms,
                status="error",
                error=str(e)
            )
            raise

