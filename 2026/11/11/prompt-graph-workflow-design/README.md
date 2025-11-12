# Prompt-Graph Workflow Design

A Python library for building robust LLM-powered workflows using graph-based architecture. Move beyond linear prompt chains to flexible, observable, and maintainable graph workflows.

## Features

- **Graph-Based Workflows**: Model complex LLM pipelines as directed graphs
- **Multiple Node Types**: Prompt, Retrieval, Tool, Decision, Memory, Transform nodes
- **Branching Logic**: Conditional execution paths based on data
- **Error Handling**: Built-in error recovery and fallback paths
- **Observability**: Comprehensive logging and execution tracing
- **Versioning**: Version nodes independently for safe updates
- **Visualization**: Visualize graph structure and execution flow

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Example

```python
from src import PromptGraph, GraphExecutor, PromptNode, RetrievalNode

# Create graph
graph = PromptGraph("my_workflow")

# Define nodes
retrieve = RetrievalNode(
    node_id="retrieve",
    query_field="query",
    top_k=5
)

prompt = PromptNode(
    node_id="generate",
    prompt_template="Context: {context}\n\nQuestion: {query}\n\nAnswer:",
    inputs=["context", "query"]
)

# Add nodes and edges
graph.add_node(retrieve)
graph.add_node(prompt)
graph.add_edge("retrieve", "generate", {"context": "context", "query": "query"})

# Execute
executor = GraphExecutor(graph)
result = executor.execute({"query": "What is AI?"})
print(result["response"])
```

### Customer Support Bot Example

```bash
python examples/customer_support_bot.py
```

This example demonstrates:
- Retrieval from FAQ database
- LLM answer generation
- Confidence-based branching
- Human escalation for low confidence

### Legal Document Assistant Example

```bash
python examples/legal_document_assistant.py
```

This example shows:
- Document metadata extraction
- Similar case retrieval
- Summary generation with confidence scoring
- Complexity-based routing
- Human review escalation

## Architecture

### Node Types

**PromptNode**: Invokes LLM with prompt template
```python
PromptNode(
    node_id="extract",
    prompt_template="Extract entities from: {text}",
    inputs=["text"],
    outputs=["entities"]
)
```

**RetrievalNode**: Fetches context from vector stores
```python
RetrievalNode(
    node_id="retrieve",
    query_field="query",
    top_k=5,
    vector_store=my_vector_store
)
```

**DecisionNode**: Branches based on conditions
```python
DecisionNode(
    node_id="check_confidence",
    condition="confidence < 0.7",
    true_branch="human_review",
    false_branch="final_answer"
)
```

**ToolNode**: Executes external functions
```python
ToolNode(
    node_id="calculate",
    tool_function=my_calculator,
    inputs=["a", "b"]
)
```

**MemoryNode**: Stores/retrieves from memory
```python
MemoryNode(
    node_id="store",
    operation="write",
    key="conversation_id",
    inputs=["messages"]
)
```

### Graph Structure

```python
graph = PromptGraph("workflow_id")

# Add nodes
graph.add_node(node1)
graph.add_node(node2)

# Add edges with data mapping
graph.add_edge("node1", "node2", {
    "output1": "input1",
    "output2": "input2"
})

# Add conditional edges
graph.add_edge("decision", "branch_a", condition="value > 0")
graph.add_edge("decision", "branch_b", condition="value <= 0")
```

### Execution

```python
executor = GraphExecutor(graph, logger=my_logger)
result = executor.execute(initial_inputs)

# Access results
print(result["final_output"])
print(executor.node_results["node_id"].status)
```

## Observability

### Logging

```python
from src import ObservabilityLogger

logger = ObservabilityLogger(log_file="execution.log")
executor = GraphExecutor(graph, logger=logger)

# Get execution trace
trace = logger.get_execution_trace(execution_id)
```

### Visualization

```python
from src import GraphVisualizer

visualizer = GraphVisualizer(graph)
visualizer.visualize_structure("graph.png")
visualizer.visualize_execution(executor, "execution.png")
```

### Lineage Tracking

```python
from src import LineageTracker

tracker = LineageTracker()
tracker.track_execution(
    execution_id="exec_123",
    graph_version="v1",
    node_versions={"node1": "v2", "node2": "v1"},
    inputs={"query": "test"},
    outputs={"result": "output"}
)
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=src tests/
```

## Environment Variables

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=your_api_key_here
```

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── nodes.py          # Node implementations
│   ├── graph.py           # Graph structure
│   ├── executor.py        # Execution engine
│   └── observability.py   # Logging and visualization
├── examples/
│   ├── customer_support_bot.py
│   └── legal_document_assistant.py
├── tests/
│   ├── test_nodes.py
│   ├── test_graph.py
│   └── test_executor.py
├── requirements.txt
└── README.md
```

## Best Practices

1. **Node Granularity**: One logical operation per node
2. **Naming**: Use descriptive node IDs (`extract_entities` not `node1`)
3. **Versioning**: Version nodes independently for safe updates
4. **Error Handling**: Design error paths explicitly
5. **Testing**: Test individual nodes and graph paths
6. **Observability**: Log all node executions and branch decisions

## Advanced Features

### Custom Retrieval Functions

```python
def my_retrieval(query: str, top_k: int) -> list:
    # Your custom retrieval logic
    return results

node = RetrievalNode(
    node_id="custom_retrieve",
    retrieval_function=my_retrieval,
    query_field="query",
    top_k=5
)
```

### Conditional Branching

```python
decision = DecisionNode(
    node_id="route",
    condition="confidence < 0.7 and complexity > 0.8",
    true_branch="human_review",
    false_branch="auto_process"
)
```

### Error Recovery

```python
# Add error edge
graph.add_edge("retrieve", "fallback", condition="error_occurred")
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License

## Related Articles

- [From Prompt-Chaining to Prompt-Graph: Next-gen Workflow Design for LLM-Powered Pipelines](https://appropri8.com/blog/2025/11/11/prompt-graph-workflow-design)

## Support

For issues and questions, please open an issue on GitHub.

