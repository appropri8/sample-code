# Budget-Aware AI Agents: Keeping Cost, Tokens, and Latency Under Control

A Python library demonstrating how to add budget management to AI agents. This implementation shows how to prevent agents from looping forever, burning tokens, and slowing everything down.

## Features

- **Run Budgets**: Define limits for steps, tokens, and time per agent run
- **Budget Manager**: Track and enforce budgets during agent execution
- **Graceful Exhaustion**: Handle budget limits gracefully with summaries
- **Multi-Tenant Quotas**: Manage quotas across multiple tenants or users
- **Configuration-Based**: Define budgets in YAML configuration files
- **Comprehensive Logging**: Track budget usage for observability

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from src.budgets import RunBudget
from src.research_agent import ResearchAgent

# Create a budget
budget = RunBudget(
    max_steps=5,
    max_tokens=2000,
    max_seconds=10
)

# Create agent with budget
agent = ResearchAgent(budget)

# Ask a question
result = agent.answer("What is machine learning?")

print(result["answer"])
print(f"Budget used: {result['budget_used']}")
```

### Using Configuration Files

```python
from src.config_loader import load_budget_config
from src.research_agent import ResearchAgent

# Load budgets from YAML
budgets = load_budget_config("budgets.yaml")

# Use a specific budget
agent = ResearchAgent(budgets["quick_answer"])
result = agent.answer("What is Python?")
```

### Multi-Tenant Quotas

```python
from src.quota_service import QuotaService
from src.budgets import RunBudget
from src.research_agent import ResearchAgent

# Create quota service
quota_service = QuotaService(default_daily_quota=10000)

# Check quota before running agent
if quota_service.check_quota("tenant_123", estimated_tokens=2000):
    budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
    agent = ResearchAgent(budget)
    result = agent.answer("What is deep learning?")
    
    # Consume quota
    quota_service.consume_quota("tenant_123", result["budget_used"]["tokens"])
```

## Examples

### Example 1: Basic Usage

```bash
python examples/basic_usage.py
```

Shows how to:
- Create a budget
- Run an agent with budget limits
- Check budget usage and remaining budget

### Example 2: Deep Research

```bash
python examples/deep_research_example.py
```

Demonstrates using a larger budget for complex research tasks.

### Example 3: Budget Exhaustion

```bash
python examples/budget_exhaustion_example.py
```

Shows how the agent handles budget exhaustion gracefully.

### Example 4: Configuration-Based Budgets

```bash
python examples/config_example.py
```

Shows how to use YAML configuration files to define different budgets for different use cases.

### Example 5: Multi-Tenant Quotas

```bash
python examples/quota_service_example.py
```

Demonstrates quota management across multiple tenants.

## Architecture

### Components

1. **RunBudget** (`src/budgets.py`): Defines budget limits
   - Max steps per run
   - Max tokens per run
   - Max time per run
   - Max nested tool calls (optional)

2. **BudgetManager** (`src/budgets.py`): Tracks and enforces budgets
   - Checks limits before each call
   - Records usage
   - Provides remaining budget information

3. **ResearchAgent** (`src/research_agent.py`): Example agent implementation
   - Searches documents
   - Synthesizes answers
   - Handles budget exhaustion gracefully

4. **QuotaService** (`src/quota_service.py`): Multi-tenant quota management
   - Daily quotas per tenant
   - Priority-based quota checking
   - Automatic quota reset

5. **Token Utils** (`src/token_utils.py`): Token estimation
   - Rough token estimation (1 token ≈ 4 characters)
   - In production, use tiktoken for accuracy

6. **Config Loader** (`src/config_loader.py`): YAML configuration loading
   - Load budgets from YAML files
   - Support for multiple budget profiles

## Design Principles

### 1. Simple Limits

Start with three simple limits:
- Max steps per run
- Max tokens per run
- Max time per run

### 2. Check Before Each Call

Always check the budget before making a model or tool call. Don't wait until after.

### 3. Graceful Exhaustion

When the budget is exhausted, don't just fail. Provide a summary or ask the user to continue with a larger budget.

### 4. Observability

Log budget usage for every step. Use this data to optimize and adjust budgets.

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

## Configuration

Create a `budgets.yaml` file:

```yaml
budgets:
  quick_answer:
    max_steps: 5
    max_tokens: 2000
    max_seconds: 10
    max_nested_tool_calls: 2
  
  deep_research:
    max_steps: 20
    max_tokens: 50000
    max_seconds: 60
    max_nested_tool_calls: 10
  
  batch_processing:
    max_steps: 50
    max_tokens: 100000
    max_seconds: 300
    max_nested_tool_calls: 20
```

## Best Practices

1. **Start with Conservative Budgets**: Set lower limits initially and increase as needed
2. **Monitor Budget Usage**: Track where tokens and time are spent
3. **Adjust Based on Data**: Use observability data to optimize budgets
4. **Handle Exhaustion Gracefully**: Always provide a fallback when budgets are exhausted
5. **Use Different Budgets for Different Use Cases**: Quick Q&A needs different limits than deep research
6. **Implement Quotas for Multi-Tenant Systems**: Prevent one tenant from consuming all resources

## Token Estimation

This implementation uses a simple token estimation (1 token ≈ 4 characters). For production use:

- Use `tiktoken` for accurate token counting
- Cache token counts for repeated content
- Account for model-specific tokenization differences

Example with tiktoken:

```python
import tiktoken

def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
```

## Limitations

- Simple token estimation (use tiktoken in production)
- In-memory quota service (extend for distributed systems)
- Simulated model calls (implement real LLM API calls)
- Basic logging (enhance for production observability)

## Extending the Implementation

### Adding Real LLM Calls

Replace the simulated model calls in `ResearchAgent.synthesize_answer()` with actual API calls:

```python
def synthesize_answer(self, query: str, documents: list, budget_manager: BudgetManager) -> str:
    # ... budget checks ...
    
    # Real LLM call
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Count actual tokens used
    tokens_used = response.usage.total_tokens
    budget_manager.record_call(tokens_used)
    
    return response.choices[0].message.content
```

### Adding Distributed Quota Service

For production, use Redis or a database for quota storage:

```python
import redis

class DistributedQuotaService:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def check_quota(self, tenant_id: str, tokens_needed: int) -> bool:
        key = f"quota:{tenant_id}"
        remaining = self.redis.get(key)
        return int(remaining or 0) >= tokens_needed
```

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Follow existing code patterns
4. Ensure budget checks are enforced

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

