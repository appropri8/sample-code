# Evaluating LLM Systems in Production

Complete executable code samples demonstrating how to move from guessing about LLM quality to measuring it using logs, labels, and simple experiments.

## Overview

This repository contains implementations of evaluation patterns for LLM systems in production:

- **Logging**: Capture every LLM call with input, output, metadata, and performance metrics
- **Feedback Collection**: Explicit feedback (thumbs up/down, ratings) and implicit signals (edits, abandonment)
- **Evaluation Harness**: Run golden sets against different models/prompts to detect regressions
- **LLM-as-Judge**: Use one model to evaluate another model's outputs
- **A/B Testing**: Split traffic between baseline and candidate variants
- **Shadow Testing**: Run candidate in background while users see baseline

Both Python and TypeScript implementations are provided.

## Installation

### Python

```bash
cd python
pip install -r requirements.txt
```

### TypeScript

```bash
cd typescript
npm install
npm run build
```

## Prerequisites

- Python 3.10+ (for Python examples)
- Node.js 18+ (for TypeScript examples)
- LLM API access (OpenAI, Anthropic, etc.) - for production use
- Optional: File system access for logging (examples use file-based logging)

## Quick Start

### Python Examples

**Logging:**
```bash
cd python
python examples/logging_example.py
```

**Feedback Collection:**
```bash
python examples/feedback_example.py
```

**Evaluation Harness:**
```bash
python examples/eval_harness_example.py
```

**LLM-as-Judge:**
```bash
python examples/llm_judge_example.py
```

**A/B Testing:**
```bash
python examples/ab_test_example.py
```

### TypeScript Examples

```bash
cd typescript
npm run build
node dist/examples/ab-test-example.js
```

## Structure

```
.
├── python/
│   ├── src/
│   │   ├── logger.py          # Logging module
│   │   ├── feedback.py        # Feedback collection
│   │   ├── eval_harness.py    # Evaluation harness
│   │   ├── llm_judge.py       # LLM-as-judge
│   │   └── experiments.py     # A/B and shadow testing
│   └── examples/
│       ├── logging_example.py
│       ├── feedback_example.py
│       ├── eval_harness_example.py
│       ├── llm_judge_example.py
│       └── ab_test_example.py
├── typescript/
│   ├── src/
│   │   ├── logger.ts
│   │   ├── feedback.ts
│   │   ├── experiments.ts
│   │   └── llm-judge.ts
│   └── examples/
│       └── ab-test-example.ts
└── README.md
```

## Key Concepts

### Logging

Log every LLM call with:
- Input query and context
- Model output
- Model name, version, parameters
- Prompt template version
- Performance metrics (latency, cost, tokens)
- Experiment variant and cohort

### Feedback

**Explicit feedback:**
- Thumbs up/down
- Ratings (1-5 scale)
- Task-specific labels (correctness, helpfulness, etc.)

**Implicit signals:**
- User edits (how much was edited)
- Abandonment (user left the flow)
- Repeat queries (user asked again)
- Time spent (how long user engaged)

### Evaluation Harness

Run a golden set (labeled examples) against:
- Baseline model/prompt
- Candidate model/prompt

Compare outputs and detect regressions before deployment.

### LLM-as-Judge

Use a strong model (e.g., GPT-4) to evaluate outputs from another model:
- Pairwise comparison: Which output is better?
- Scoring: Rate output on a scale
- Labeling: Categorize output (correct/incorrect, helpful/not helpful)

### A/B Testing

Split traffic between baseline and candidate:
- Deterministic assignment (same user always gets same variant)
- Compare metrics (success rate, user satisfaction, etc.)
- Make data-driven decisions

### Shadow Testing

Run candidate in background while users see baseline:
- Safe validation before exposing users
- Compare outputs offline
- Move to A/B test if results look good

## Usage Examples

### Logging LLM Calls

```python
from src.logger import LLMLogger

logger = LLMLogger(log_file="llm_logs.jsonl")

log = logger.log_call(
    request_id="req_123",
    user_id="user_456",
    query="How do I reset my password?",
    response="To reset your password...",
    model_name="gpt-4",
    model_version="2024-11-20",
    prompt_version="v1.0",
    latency_ms=1250,
    tokens_used=150,
    cost_usd=0.002,
    experiment_variant="baseline"
)
```

### Collecting Feedback

```python
from src.feedback import FeedbackCollector

collector = FeedbackCollector()

# Explicit feedback
collector.record_thumbs_up("req_123", True)
collector.record_rating("req_123", 5)
collector.record_labels("req_123", {
    "correctness": "correct",
    "helpfulness": "helpful"
})

# Implicit signals
collector.record_edit("req_123", edit_ratio=0.2)
collector.record_abandon("req_124")
```

### Running Evaluation Harness

```python
from src.eval_harness import EvaluationHarness

harness = EvaluationHarness("golden_set.json")
results = harness.run_evaluation(
    baseline_model=baseline_model,
    candidate_model=candidate_model,
    labeler=llm_judge_labeler
)

harness.print_results(results)
passed = harness.check_regressions(results, min_pass_rate=0.95)
```

### Using LLM-as-Judge

```python
from src.llm_judge import LLMJudge

judge = LLMJudge(llm_function)

# Pairwise comparison
winner = judge.pairwise(
    input_text="How do I reset my password?",
    output_a="Baseline response...",
    output_b="Candidate response...",
    criteria="Which is more helpful?"
)

# Scoring
score = judge.score(
    input_text="How do I reset my password?",
    output="To reset your password...",
    criteria="Rate helpfulness",
    scale="1-5"
)
```

### A/B Testing

```python
from src.experiments import ABTest

ab_test = ABTest(
    experiment_name="prompt_v2",
    baseline_model=baseline_model,
    candidate_model=candidate_model,
    split_ratio=0.5
)

output, assignment = ab_test.run("user_123", "How do I reset my password?")
# assignment.variant is "baseline" or "candidate"
```

### Shadow Testing

```python
from src.experiments import ShadowTest

shadow_test = ShadowTest(
    experiment_name="new_model_test",
    baseline_model=baseline_model,
    candidate_model=candidate_model,
    logger=comparison_logger
)

baseline_output, comparison = shadow_test.run("user_123", "How do I reset my password?")
# User sees baseline_output, candidate runs in background
```

## Golden Set Format

A golden set is a JSON file with labeled examples:

```json
[
  {
    "id": "example_001",
    "input": {
      "query": "How do I reset my password?"
    },
    "expected_behavior": "Provide clear steps to reset password",
    "outputs": [
      {
        "variant": "baseline",
        "text": "To reset your password...",
        "labels": {
          "correctness": "correct",
          "helpfulness": "helpful"
        }
      }
    ]
  }
]
```

## Production Considerations

### Privacy

- Redact PII (emails, phone numbers, credit cards) from logs
- Hash user IDs before logging
- Restrict access to raw logs
- Use audit logs for access tracking

### Performance

- Log asynchronously to avoid blocking requests
- Batch log writes for efficiency
- Use structured logging (JSON) for easy querying
- Set up log rotation and retention policies

### Monitoring

- Track error rates (parse failures, validation failures)
- Monitor user signals (thumbs up/down rates, abandonment)
- Set up alerts for quality degradation
- Track key metrics over time

### Evaluation

- Run evaluation harness before every deployment
- Check for regressions on golden set
- Use LLM-as-judge for scale, humans for quality
- Combine explicit and implicit feedback

## License

MIT

## Contributing

This is example code for educational purposes. Feel free to adapt it for your use case.

