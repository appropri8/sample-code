"""Workflow implementation with versioning and state management"""
from typing import List, Dict, Any, Callable, Optional
import yaml
import json


class WorkflowNode:
    """Node in workflow graph"""
    
    def __init__(
        self,
        name: str,
        agent: Any,  # Agent instance
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    ):
        self.name = name
        self.agent = agent
        self.condition = condition


class Workflow:
    """Workflow with explicit versioning"""
    
    def __init__(
        self,
        name: str,
        nodes: List[WorkflowNode],
        edges: List[tuple],
        version: str
    ):
        self.name = name
        self.nodes = nodes
        self.edges = edges
        self.version = version
        self.node_map = {node.name: node for node in nodes}
    
    def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow"""
        current_state = initial_state.copy()
        current_state["workflow_version"] = self.version
        current_state["trace_id"] = current_state.get("trace_id", f"trace_{id(self)}")
        
        if not self.nodes:
            return current_state
        
        current_node = self.nodes[0]
        execution_path = []
        
        while current_node:
            execution_path.append(current_node.name)
            
            # Check condition
            if current_node.condition and not current_node.condition(current_state):
                break
            
            # Execute node
            try:
                result = current_node.agent.run(current_state)
                current_state.update(result.get("result", {}))
                current_state["last_node"] = current_node.name
                current_state["last_result"] = result
            except Exception as e:
                current_state["error"] = str(e)
                break
            
            # Find next node
            next_node = self._get_next_node(current_node, current_state)
            if next_node is None:
                break
            current_node = next_node
        
        current_state["execution_path"] = execution_path
        return current_state
    
    def _get_next_node(
        self,
        current_node: WorkflowNode,
        state: Dict[str, Any]
    ) -> Optional[WorkflowNode]:
        """Get next node based on edges"""
        for edge in self.edges:
            if len(edge) >= 2 and edge[0] == current_node.name:
                next_name = edge[1]
                if next_name in self.node_map:
                    return self.node_map[next_name]
        return None
    
    @classmethod
    def from_yaml(cls, yaml_path: str, agent_factory: Callable) -> 'Workflow':
        """Load workflow from YAML"""
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        nodes = []
        for node_config in config.get("nodes", []):
            agent = agent_factory(node_config["agent"])
            condition = None  # Could parse condition from config
            nodes.append(WorkflowNode(
                name=node_config["name"],
                agent=agent,
                condition=condition
            ))
        
        edges = config.get("edges", [])
        
        return cls(
            name=config["name"],
            nodes=nodes,
            edges=edges,
            version=config["version"]
        )

