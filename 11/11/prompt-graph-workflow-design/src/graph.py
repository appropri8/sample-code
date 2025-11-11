"""Graph definition and structure for prompt-graph workflows"""

from typing import Dict, List, Tuple, Optional, Any
import networkx as nx
from .nodes import Node


class PromptGraph:
    """Directed graph representing a prompt-graph workflow"""
    
    def __init__(self, graph_id: str, version: str = "v1"):
        self.graph_id = graph_id
        self.version = version
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Tuple[str, str, Dict]] = []
        self.graph = nx.DiGraph()
    
    def add_node(self, node: Node):
        """Add a node to the graph"""
        self.nodes[node.node_id] = node
        self.graph.add_node(node.node_id)
    
    def add_edge(
        self,
        from_node: str,
        to_node: str,
        data_mapping: Dict[str, str] = None,
        condition: str = None
    ):
        """Add an edge between nodes"""
        if from_node not in self.nodes:
            raise ValueError(f"Source node '{from_node}' not found in graph")
        if to_node not in self.nodes:
            raise ValueError(f"Target node '{to_node}' not found in graph")
        
        edge_data = {
            "data_mapping": data_mapping or {},
            "condition": condition
        }
        self.edges.append((from_node, to_node, edge_data))
        self.graph.add_edge(from_node, to_node, **edge_data)
    
    def get_entry_nodes(self) -> List[str]:
        """Find nodes with no incoming edges"""
        return [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
    
    def get_next_nodes(self, node_id: str, context: Dict[str, Any] = None) -> List[str]:
        """Get nodes that should execute after this one"""
        if context is None:
            context = {}
        
        next_nodes = []
        for from_n, to_n, edge_data in self.edges:
            if from_n == node_id:
                # Check condition if present
                if edge_data.get("condition"):
                    try:
                        safe_dict = {"__builtins__": {}}
                        safe_dict.update(context)
                        if not eval(edge_data["condition"], safe_dict, {}):
                            continue
                    except:
                        continue
                next_nodes.append(to_n)
        return next_nodes
    
    def get_predecessors(self, node_id: str) -> List[str]:
        """Get nodes that come before this one"""
        return list(self.graph.predecessors(node_id))
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate graph structure"""
        errors = []
        
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                errors.append(f"Graph contains cycles: {cycles}")
        except:
            pass
        
        # Check all edges reference valid nodes
        for from_n, to_n, _ in self.edges:
            if from_n not in self.nodes:
                errors.append(f"Edge references unknown source node: {from_n}")
            if to_n not in self.nodes:
                errors.append(f"Edge references unknown target node: {to_n}")
        
        # Check for isolated nodes (no edges)
        isolated = [n for n in self.graph.nodes() if self.graph.degree(n) == 0]
        if isolated and len(self.nodes) > 1:
            errors.append(f"Isolated nodes found: {isolated}")
        
        return len(errors) == 0, errors

