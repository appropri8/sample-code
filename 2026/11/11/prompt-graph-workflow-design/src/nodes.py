"""Node implementations for prompt-graph workflows"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
import time


class NodeStatus(Enum):
    """Status of a node execution"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    """Result of a node execution"""
    status: NodeStatus
    output: Dict[str, Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Node(ABC):
    """Base class for all graph nodes"""
    
    def __init__(
        self,
        node_id: str,
        inputs: List[str],
        outputs: List[str],
        version: str = "v1"
    ):
        self.node_id = node_id
        self.inputs = inputs
        self.outputs = outputs
        self.version = version
        self.status = NodeStatus.PENDING
        self.result: Optional[NodeResult] = None
    
    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> NodeResult:
        """Execute the node with given inputs"""
        pass
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate that required inputs are present"""
        for input_key in self.inputs:
            if input_key not in inputs:
                return False
        return True


class PromptNode(Node):
    """Node that invokes an LLM with a prompt template"""
    
    def __init__(
        self,
        node_id: str,
        prompt_template: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        inputs: List[str] = None,
        outputs: List[str] = None,
        version: str = "v1",
        api_key: Optional[str] = None
    ):
        super().__init__(node_id, inputs or [], outputs or ["response"], version)
        self.prompt_template = prompt_template
        self.model = model
        self.temperature = temperature
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        except ImportError:
            raise ImportError(
                "openai package is required for PromptNode. "
                "Install it with: pip install openai"
            )
    
    def execute(self, inputs: Dict[str, Any]) -> NodeResult:
        try:
            if not self.validate_inputs(inputs):
                missing = [k for k in self.inputs if k not in inputs]
                return NodeResult(
                    status=NodeStatus.FAILED,
                    output={},
                    error=f"Missing required inputs: {missing}"
                )
            
            # Format prompt template with inputs
            prompt = self.prompt_template.format(**inputs)
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            
            # Parse output if needed
            output = {"response": content}
            
            # Try to extract structured data if outputs are specified
            if len(self.outputs) > 1:
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        output.update(parsed)
                except (json.JSONDecodeError, ValueError):
                    # If not JSON, try to extract key-value pairs
                    pass
            
            return NodeResult(
                status=NodeStatus.SUCCESS,
                output=output,
                metadata={
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0,
                    "prompt_version": self.version,
                    "prompt_length": len(prompt)
                }
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                output={},
                error=str(e),
                metadata={"node_id": self.node_id, "version": self.version}
            )


class RetrievalNode(Node):
    """Node that retrieves context from vector stores or databases"""
    
    def __init__(
        self,
        node_id: str,
        vector_store=None,
        query_field: str = "query",
        top_k: int = 5,
        inputs: List[str] = None,
        outputs: List[str] = None,
        version: str = "v1",
        retrieval_function: Optional[Callable] = None
    ):
        super().__init__(node_id, inputs or [query_field], outputs or ["context"], version)
        self.vector_store = vector_store
        self.query_field = query_field
        self.top_k = top_k
        self.retrieval_function = retrieval_function
    
    def execute(self, inputs: Dict[str, Any]) -> NodeResult:
        try:
            if not self.validate_inputs(inputs):
                missing = [k for k in self.inputs if k not in inputs]
                return NodeResult(
                    status=NodeStatus.FAILED,
                    output={},
                    error=f"Missing required inputs: {missing}"
                )
            
            query = inputs[self.query_field]
            
            # Use custom retrieval function if provided
            if self.retrieval_function:
                docs = self.retrieval_function(query, self.top_k)
            elif self.vector_store:
                # Similarity search
                docs = self.vector_store.similarity_search(query, k=self.top_k)
            else:
                # Mock retrieval for testing
                docs = [f"Mock document {i} about {query}" for i in range(min(3, self.top_k))]
            
            # Combine into context
            if hasattr(docs[0], 'page_content'):
                context = "\n\n".join([doc.page_content for doc in docs])
                doc_contents = [doc.page_content for doc in docs]
            else:
                context = "\n\n".join(docs)
                doc_contents = docs
            
            return NodeResult(
                status=NodeStatus.SUCCESS,
                output={"context": context, "documents": doc_contents},
                metadata={
                    "top_k": self.top_k,
                    "results_found": len(docs),
                    "query": query[:100]  # Truncate for logging
                }
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                output={},
                error=str(e),
                metadata={"node_id": self.node_id, "version": self.version}
            )


class DecisionNode(Node):
    """Node that branches execution based on conditions"""
    
    def __init__(
        self,
        node_id: str,
        condition: str,  # Python expression like "confidence < 0.7"
        true_branch: str,
        false_branch: str,
        inputs: List[str] = None,
        outputs: List[str] = None,
        version: str = "v1"
    ):
        super().__init__(node_id, inputs or [], outputs or ["branch"], version)
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch
    
    def execute(self, inputs: Dict[str, Any]) -> NodeResult:
        try:
            # Evaluate condition with inputs as context
            # Use safe evaluation
            safe_dict = {"__builtins__": {}}
            safe_dict.update(inputs)
            result = eval(self.condition, safe_dict, {})
            
            branch = self.true_branch if result else self.false_branch
            
            return NodeResult(
                status=NodeStatus.SUCCESS,
                output={"branch": branch, "condition_result": result},
                metadata={
                    "condition": self.condition,
                    "result": result,
                    "selected_branch": branch
                }
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                output={},
                error=f"Failed to evaluate condition '{self.condition}': {str(e)}",
                metadata={"node_id": self.node_id, "version": self.version}
            )


class ToolNode(Node):
    """Node that executes external tools or functions"""
    
    def __init__(
        self,
        node_id: str,
        tool_function: Callable,
        inputs: List[str],
        outputs: List[str] = None,
        version: str = "v1"
    ):
        super().__init__(node_id, inputs, outputs or ["result"], version)
        self.tool_function = tool_function
    
    def execute(self, inputs: Dict[str, Any]) -> NodeResult:
        try:
            if not self.validate_inputs(inputs):
                missing = [k for k in self.inputs if k not in inputs]
                return NodeResult(
                    status=NodeStatus.FAILED,
                    output={},
                    error=f"Missing required inputs: {missing}"
                )
            
            # Extract inputs in order
            args = [inputs[key] for key in self.inputs]
            
            # Call tool
            result = self.tool_function(*args)
            
            return NodeResult(
                status=NodeStatus.SUCCESS,
                output={"result": result},
                metadata={
                    "tool": self.tool_function.__name__ if hasattr(self.tool_function, '__name__') else "anonymous",
                    "inputs_count": len(args)
                }
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                output={},
                error=str(e),
                metadata={"node_id": self.node_id, "version": self.version}
            )


class MemoryNode(Node):
    """Node that stores or retrieves information from memory"""
    
    def __init__(
        self,
        node_id: str,
        operation: str,  # "read" or "write"
        key: str,
        inputs: List[str] = None,
        outputs: List[str] = None,
        version: str = "v1",
        memory_store: Optional[Dict] = None
    ):
        super().__init__(node_id, inputs or [], outputs or ["memory_result"], version)
        self.operation = operation
        self.key = key
        self.memory_store = memory_store if memory_store is not None else {}
    
    def execute(self, inputs: Dict[str, Any]) -> NodeResult:
        try:
            if self.operation == "write":
                if not self.validate_inputs(inputs):
                    missing = [k for k in self.inputs if k not in inputs]
                    return NodeResult(
                        status=NodeStatus.FAILED,
                        output={},
                        error=f"Missing required inputs: {missing}"
                    )
                # Store data
                self.memory_store[self.key] = inputs
                return NodeResult(
                    status=NodeStatus.SUCCESS,
                    output={"memory_result": "stored", "key": self.key},
                    metadata={"operation": "write", "key": self.key}
                )
            elif self.operation == "read":
                # Retrieve data
                data = self.memory_store.get(self.key, {})
                return NodeResult(
                    status=NodeStatus.SUCCESS,
                    output={"memory_result": data, "key": self.key},
                    metadata={"operation": "read", "key": self.key}
                )
            else:
                return NodeResult(
                    status=NodeStatus.FAILED,
                    output={},
                    error=f"Unknown operation: {self.operation}"
                )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                output={},
                error=str(e),
                metadata={"node_id": self.node_id, "version": self.version}
            )


class TransformNode(Node):
    """Node that processes data between steps"""
    
    def __init__(
        self,
        node_id: str,
        transform_function: Callable,
        inputs: List[str],
        outputs: List[str] = None,
        version: str = "v1"
    ):
        super().__init__(node_id, inputs, outputs or ["transformed"], version)
        self.transform_function = transform_function
    
    def execute(self, inputs: Dict[str, Any]) -> NodeResult:
        try:
            if not self.validate_inputs(inputs):
                missing = [k for k in self.inputs if k not in inputs]
                return NodeResult(
                    status=NodeStatus.FAILED,
                    output={},
                    error=f"Missing required inputs: {missing}"
                )
            
            # Apply transform
            result = self.transform_function(inputs)
            
            if not isinstance(result, dict):
                result = {"transformed": result}
            
            return NodeResult(
                status=NodeStatus.SUCCESS,
                output=result,
                metadata={
                    "transform": self.transform_function.__name__ if hasattr(self.transform_function, '__name__') else "anonymous"
                }
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                output={},
                error=str(e),
                metadata={"node_id": self.node_id, "version": self.version}
            )

