"""
Example 10: Complete Pipeline

End-to-end example tying everything together:
- Prompt construction with schema
- LLM generation (mocked)
- Parsing
- Validation
- Retry with repair
- Metrics collection
- Error handling
"""

import json
import time
from datetime import datetime
from typing import TypeVar
from pydantic import BaseModel, Field
from typing import Literal

# Import our modules
import sys
sys.path.insert(0, '.')

T = TypeVar('T', bound=BaseModel)


# Define our schema
class TaskExtraction(BaseModel):
    """Extract task information from text"""
    
    version: Literal["2.0"] = "2.0"
    title: str = Field(min_length=5, max_length=100)
    priority: Literal[1, 2, 3, 4, 5]
    category: Literal["bug", "feature", "docs", "refactor"]
    description: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=5)


class CompletePipeline:
    """Complete extraction pipeline with all features"""
    
    def __init__(self, metrics_collector=None):
        self.metrics_collector = metrics_collector
        self.extraction_count = 0
    
    def build_prompt(self, user_input: str, schema: type[BaseModel]) -> str:
        """Build prompt with schema"""
        schema_json = schema.model_json_schema()
        
        return f"""Extract structured task information from the following text.

Return valid JSON that matches this schema:
{json.dumps(schema_json, indent=2)}

Text to extract from:
{user_input}

Return only valid JSON, no other text."""
    
    def mock_llm_call(self, prompt: str, attempt: int = 0) -> str:
        """
        Mock LLM call that simulates real behavior
        - First attempt might have errors
        - Repair attempts fix the errors
        """
        
        # Simulate latency
        time.sleep(0.1)
        
        if "validation errors" in prompt.lower():
            # This is a repair attempt - return valid output
            return """{
                "version": "2.0",
                "title": "Fix authentication bug in login service",
                "priority": 4,
                "category": "bug",
                "description": "Users cannot log in with social authentication",
                "tags": ["auth", "urgent", "security"]
            }"""
        
        # Simulate occasional errors on first attempt
        if attempt == 0 and self.extraction_count % 5 == 0:
            # Return invalid priority (string instead of number)
            return """Here's the extracted information:
```json
{
    "version": "2.0",
    "title": "Fix authentication bug in login service",
    "priority": "high",
    "category": "bug"
}
```"""
        
        # Normal valid response
        return """{
            "version": "2.0",
            "title": "Fix authentication bug in login service",
            "priority": 4,
            "category": "bug",
            "description": "Users cannot log in with social authentication",
            "tags": ["auth", "urgent"]
        }"""
    
    def extract(
        self,
        user_input: str,
        schema: type[T],
        max_retries: int = 2
    ) -> tuple[T | None, dict]:
        """
        Complete extraction with retry and metrics
        
        Returns:
            Tuple of (result, metadata)
        """
        from src.validation_middleware import ValidationMiddleware
        from src.retry_logic import RetryStrategy, RetryConfig
        
        self.extraction_count += 1
        start_time = time.time()
        
        metadata = {
            "extraction_id": self.extraction_count,
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input[:100],  # Truncate for logging
            "schema_version": "2.0",
            "attempts": 0,
            "success": False,
            "errors": [],
            "latency_ms": 0
        }
        
        # Build initial prompt
        prompt = self.build_prompt(user_input, schema)
        current_prompt = prompt
        
        # Try with retries
        for attempt in range(max_retries + 1):
            metadata["attempts"] = attempt + 1
            
            # Call LLM
            response = self.mock_llm_call(current_prompt, attempt)
            
            # Validate
            result = ValidationMiddleware.validate(response, schema)
            
            if result.success:
                metadata["success"] = True
                metadata["latency_ms"] = (time.time() - start_time) * 1000
                
                # Record metrics
                if self.metrics_collector:
                    from src.observability_metrics import ExtractionMetrics
                    self.metrics_collector.record(ExtractionMetrics(
                        timestamp=datetime.now(),
                        success=True,
                        validation_passed=True,
                        parse_passed=True,
                        retry_count=attempt,
                        latency_ms=metadata["latency_ms"],
                        schema_version="2.0",
                        fields_populated=set(result.data.model_fields_set)
                    ))
                
                return result.data, metadata
            
            # Record errors
            metadata["errors"].extend(result.errors)
            
            # If last attempt, give up
            if attempt >= max_retries:
                metadata["latency_ms"] = (time.time() - start_time) * 1000
                
                # Record failure metrics
                if self.metrics_collector:
                    from src.observability_metrics import ExtractionMetrics
                    self.metrics_collector.record(ExtractionMetrics(
                        timestamp=datetime.now(),
                        success=False,
                        validation_passed=False,
                        parse_passed=result.errors[0] != "Failed to parse valid JSON from output",
                        retry_count=attempt,
                        latency_ms=metadata["latency_ms"],
                        schema_version="2.0",
                        error_type=result.errors[0] if result.errors else "unknown"
                    ))
                
                return None, metadata
            
            # Build repair prompt
            current_prompt = RetryStrategy.build_repair_prompt(
                prompt,
                result.errors,
                schema
            )
            
            # Exponential backoff
            time.sleep(0.1 * (2 ** attempt))
        
        return None, metadata


def demonstrate_complete_pipeline():
    """Demonstrate the complete pipeline"""
    
    from src.observability_metrics import MetricsCollector, AlertingThresholds
    
    print("=" * 60)
    print("Example 10: Complete Pipeline")
    print("=" * 60)
    
    # Create pipeline with metrics
    metrics = MetricsCollector()
    pipeline = CompletePipeline(metrics_collector=metrics)
    
    # Test inputs
    test_cases = [
        "High priority: Fix the critical authentication bug in the login service",
        "Add new dashboard feature for user analytics",
        "Update documentation for API endpoints",
        "Refactor database connection pooling logic",
        "URGENT: Users can't log in after last deploy",
        "Low priority: Fix typo in footer",
        "Implement search functionality",
        "Bug: Memory leak in image processing",
        "Update README with installation instructions",
        "Feature request: Dark mode support",
    ]
    
    print("\n1. Running Extractions:")
    print("-" * 60)
    
    successful = 0
    failed = 0
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n   Extraction {i}:")
        print(f"   Input: {test_input[:60]}...")
        
        result, metadata = pipeline.extract(test_input, TaskExtraction)
        
        if result:
            print(f"   ✅ Success (attempts: {metadata['attempts']}, latency: {metadata['latency_ms']:.0f}ms)")
            print(f"      Title: {result.title[:50]}...")
            print(f"      Priority: {result.priority}, Category: {result.category}")
            successful += 1
        else:
            print(f"   ❌ Failed (attempts: {metadata['attempts']}, latency: {metadata['latency_ms']:.0f}ms)")
            print(f"      Errors: {metadata['errors'][:2]}")  # Show first 2 errors
            failed += 1
    
    print("\n" + "-" * 60)
    print(f"   Total: {successful} successful, {failed} failed")
    
    # Show metrics
    print("\n2. Metrics Summary:")
    print("-" * 60)
    summary = metrics.summary()
    print(f"   Validation success rate: {summary['validation_success_rate']:.1%}")
    print(f"   Retry rate: {summary['retry_rate']:.1%}")
    print(f"   Parse failure rate: {summary['parse_failure_rate']:.1%}")
    
    latencies = summary['latency_percentiles']
    print(f"\n   Latency:")
    print(f"     P50: {latencies['p50']:.0f}ms")
    print(f"     P95: {latencies['p95']:.0f}ms")
    print(f"     P99: {latencies['p99']:.0f}ms")
    print(f"     Avg: {latencies['avg']:.0f}ms")
    
    print(f"\n   Field Population Rates:")
    for field, rate in sorted(summary['field_population_rates'].items()):
        print(f"     {field}: {rate:.1%}")
    
    # Check alerts
    print("\n3. Alert Check:")
    print("-" * 60)
    thresholds = AlertingThresholds(
        min_validation_success_rate=0.8,
        max_retry_rate=0.25,
        max_parse_failure_rate=0.1,
        max_p95_latency_ms=2000.0
    )
    
    alerts = thresholds.check_alerts(metrics)
    if alerts:
        print("   🚨 Alerts:")
        for alert in alerts:
            print(f"     - {alert}")
    else:
        print("   ✅ All metrics within thresholds")
    
    # Show example metadata
    print("\n4. Example Metadata:")
    print("-" * 60)
    result, metadata = pipeline.extract(
        "Critical bug: Fix the payment processing error",
        TaskExtraction
    )
    print(json.dumps(metadata, indent=2))
    
    print("\n" + "=" * 60)
    print("Complete pipeline demonstration finished!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_complete_pipeline()
