# Building Safe Prompt Pipelines

A Python library for building secure, adversarial-resilient prompt pipelines for LLM applications. This library provides input sanitisation, role separation, anomaly detection, and monitoring to defend against prompt injection attacks and other adversarial inputs.

## Features

- **Input Sanitisation**: Detect and clean suspicious patterns before processing
- **Role Separation**: Enforce clear boundaries between system and user content
- **Anomaly Detection**: Identify unusual usage patterns and potential attacks
- **Rate Limiting**: Prevent abuse through request throttling
- **Output Filtering**: Validate and filter model outputs for safety
- **Monitoring**: Comprehensive logging and metrics tracking
- **Human Review**: Flag high-risk requests for manual review

## Installation

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Basic Safe Pipeline

```python
from src import SafePromptPipeline

# Initialize pipeline
pipeline = SafePromptPipeline(api_key="your-api-key")

# Generate response
result = pipeline.generate("What is the capital of France?")
print(result["response"])
print(f"Warnings: {result['warnings']}")
```

### Monitored Pipeline with Anomaly Detection

```python
from src import MonitoredPromptPipeline

# Initialize monitored pipeline
pipeline = MonitoredPromptPipeline(api_key="your-api-key")

# Generate with user tracking
result = pipeline.generate(
    user_input="What is 2+2?",
    user_id="user123"
)

print(result["response"])
print(f"Anomaly detected: {result['anomaly_detection']['is_anomaly']}")
print(f"Risk score: {result['anomaly_detection']['risk_score']}")
```

### Customer Service Bot Example

See `examples/customer_service_bot.py` for a complete example of a customer service bot with:
- Rate limiting
- Anomaly detection
- Human review flagging
- Monitoring metrics

```bash
python examples/customer_service_bot.py
```

## Architecture

### Components

1. **InputSanitiser**: Cleans and validates user inputs
   - Detects suspicious patterns (injection attempts)
   - Normalises whitespace and encoding
   - Truncates overly long inputs

2. **SafePromptPipeline**: Core pipeline with safety features
   - Input sanitisation
   - Role separation (system vs user)
   - Output filtering
   - Structured logging

3. **MonitoredPromptPipeline**: Extended pipeline with monitoring
   - Anomaly detection
   - Usage metrics
   - Risk scoring

4. **AnomalyDetector**: Detects unusual patterns
   - Suspicious pattern detection
   - Rate limiting checks
   - Input repetition detection

5. **RateLimiter**: Prevents abuse
   - Per-user rate limiting
   - Configurable windows

6. **OutputFilter**: Validates outputs
   - Pattern-based filtering
   - Safety checks

7. **HumanReviewFlag**: Flags high-risk requests
   - Risk-based flagging
   - Review queue management

## Usage Examples

### Vulnerable vs Safe Implementation

Compare naive (vulnerable) and safe implementations:

```bash
python examples/naive_vs_safe.py
```

### Testing Against Adversarial Inputs

Test your pipeline against various injection attempts:

```bash
python examples/test_adversarial_inputs.py
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

### Test Categories

- **Unit Tests**: Test individual components
  - `test_sanitiser.py`: Input sanitisation
  - `test_pipeline.py`: Pipeline functionality
  - `test_monitoring.py`: Monitoring and anomaly detection
  - `test_rate_limiter.py`: Rate limiting

- **Adversarial Tests**: Test against attack patterns
  - `test_adversarial.py`: Injection attempts and fuzzing

## Design Principles

This library implements four key principles for safe prompt pipelines:

1. **Least-Privilege Context**: Limit what user input can influence
2. **Input Normalisation and Sanitisation**: Pre-process all inputs
3. **Segmentation of Roles**: Separate system and user content
4. **Monitoring & Anomaly Detection**: Track usage and detect attacks

## Security Considerations

### Detected Threats

The library defends against:

- **Prompt Injection**: Instructions that override system behavior
- **Malicious Context**: Manipulated data in context
- **Input Harvesting**: Attempts to extract system prompts
- **Out-of-Distribution Inputs**: Unexpected query patterns
- **Rate Limit Abuse**: Excessive request patterns

### Limitations

- Pattern-based detection may have false positives/negatives
- Some sophisticated attacks may bypass detection
- Requires ongoing monitoring and pattern updates
- Not a replacement for comprehensive security practices

## Best Practices

1. **Always sanitise inputs** before passing to LLMs
2. **Use role separation** (system vs user messages)
3. **Monitor usage patterns** for anomalies
4. **Set appropriate rate limits** to prevent abuse
5. **Flag high-risk requests** for human review
6. **Test against adversarial inputs** regularly
7. **Update suspicious patterns** as new attacks emerge
8. **Log all requests** for audit and analysis

## Contributing

When adding new suspicious patterns or features:

1. Add tests for new functionality
2. Update documentation
3. Test against known attack patterns
4. Consider false positive rates

## License

This code is provided as example code for educational purposes. Adapt it to your specific security requirements and threat model.

## References

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [ISACA Enterprise LLM Deployment Considerations](https://www.isaca.org/resources/news-and-trends/industry-news/2023/enterprise-llm-deployment-considerations)

