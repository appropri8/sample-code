"""Execution engine for prompt-graph workflows"""

from typing import Dict, Any, List, Optional
from collections import deque
import time
import logging

from .graph import PromptGraph
from .nodes import Node, NodeStatus, NodeResult


class GraphExecutor:
    """Executes prompt-graph workflows"""
    
    def __init__(self, graph: PromptGraph, logger=None):
        self.graph = graph
        self.logger = logger or logging.getLogger(__name__)
        self.execution_state: Dict[str, Any] = {}
        self.node_results: Dict[str, NodeResult] = {}
        self.execution_id: Optional[str] = None
    
    def execute(self, initial_inputs: Dict[str, Any], execution_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute the graph starting from entry nodes"""
        self.execution_id = execution_id or f"exec_{int(time.time())}"
        self.execution_state = initial_inputs.copy()
        self.node_results = {}
        
        # Validate graph
        is_valid, errors = self.graph.validate()
        if not is_valid:
            raise ValueError(f"Graph validation failed: {errors}")
        
        # Find entry nodes
        entry_nodes = self.graph.get_entry_nodes()
        if not entry_nodes:
            raise ValueError("No entry nodes found in graph")
        
        self.logger.info(f"Starting execution {self.execution_id} with entry nodes: {entry_nodes}")
        
        # Queue of nodes to execute
        queue = deque(entry_nodes)
        executed = set()
        failed_nodes = set()
        
        while queue:
            node_id = queue.popleft()
            
            if node_id in executed:
                continue
            
            # Check if dependencies are ready
            if not self._dependencies_ready(node_id):
                # Re-queue for later
                if node_id not in failed_nodes:
                    queue.append(node_id)
                continue
            
            # Execute node
            node = self.graph.nodes[node_id]
            inputs = self._prepare_inputs(node, node_id)
            
            self._log_execution_start(node_id, inputs)
            
            start_time = time.time()
            result = node.execute(inputs)
            duration = time.time() - start_time
            
            self.node_results[node_id] = result
            executed.add(node_id)
            
            # Update execution state with outputs
            for output_key, output_value in result.output.items():
                self.execution_state[output_key] = output_value
            
            self._log_execution_end(node_id, result, duration)
            
            # Handle errors
            if result.status == NodeStatus.FAILED:
                failed_nodes.add(node_id)
                # Find error edges
                error_context = self.execution_state.copy()
                error_context["error_occurred"] = True
                error_nodes = self.graph.get_next_nodes(node_id, error_context)
                for error_node in error_nodes:
                    if error_node not in executed and error_node not in queue:
                        queue.append(error_node)
                continue
            
            # Get next nodes
            next_nodes = self.graph.get_next_nodes(node_id, self.execution_state)
            for next_node in next_nodes:
                if next_node not in executed and next_node not in queue:
                    queue.append(next_node)
        
        # Check if all nodes executed successfully
        all_success = all(
            r.status == NodeStatus.SUCCESS 
            for r in self.node_results.values()
        )
        
        if not all_success:
            failed = [nid for nid, r in self.node_results.items() if r.status == NodeStatus.FAILED]
            self.logger.warning(f"Execution completed with failed nodes: {failed}")
        
        return self.execution_state
    
    def _dependencies_ready(self, node_id: str) -> bool:
        """Check if all dependencies for a node have executed"""
        predecessors = self.graph.get_predecessors(node_id)
        if not predecessors:
            return True
        
        for pred in predecessors:
            if pred not in self.node_results:
                return False
            if self.node_results[pred].status == NodeStatus.FAILED:
                # Check if there's an error path
                error_context = self.execution_state.copy()
                error_context["error_occurred"] = True
                error_paths = self.graph.get_next_nodes(pred, error_context)
                if node_id not in error_paths:
                    return False
        return True
    
    def _prepare_inputs(self, node: Node, node_id: str) -> Dict[str, Any]:
        """Prepare inputs for a node based on incoming edges"""
        inputs = {}
        
        # Find incoming edges
        for from_n, to_n, edge_data in self.graph.edges:
            if to_n == node_id:
                data_mapping = edge_data.get("data_mapping", {})
                if data_mapping:
                    # Map specific fields
                    for from_key, to_key in data_mapping.items():
                        if from_key in self.execution_state:
                            inputs[to_key] = self.execution_state[from_key]
                else:
                    # If no mapping, pass all outputs from predecessor
                    pred_result = self.node_results.get(from_n)
                    if pred_result:
                        inputs.update(pred_result.output)
        
        return inputs
    
    def _log_execution_start(self, node_id: str, inputs: Dict[str, Any]):
        """Log node execution start"""
        self.logger.info(
            f"Executing node: {node_id}",
            extra={
                "execution_id": self.execution_id,
                "node_id": node_id,
                "inputs_keys": list(inputs.keys()),
                "timestamp": time.time()
            }
        )
    
    def _log_execution_end(self, node_id: str, result: NodeResult, duration: float):
        """Log node execution end"""
        self.logger.info(
            f"Node completed: {node_id}",
            extra={
                "execution_id": self.execution_id,
                "node_id": node_id,
                "status": result.status.value,
                "duration": duration,
                "metadata": result.metadata,
                "error": result.error
            }
        )

