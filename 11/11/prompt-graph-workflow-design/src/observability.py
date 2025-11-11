"""Observability, logging, and visualization for prompt-graph workflows"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

from .graph import PromptGraph
from .executor import GraphExecutor
from .nodes import NodeStatus


class ObservabilityLogger:
    """Logger for tracking graph execution"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger("prompt_graph")
        self.events: List[Dict] = []
        self.log_file = log_file
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_node_execution(
        self,
        node_id: str,
        node_version: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        status: NodeStatus,
        duration: float,
        metadata: Dict[str, Any] = None,
        error: str = None,
        execution_id: Optional[str] = None
    ):
        """Log a node execution event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "execution_id": execution_id,
            "node_id": node_id,
            "node_version": node_version,
            "status": status.value,
            "duration_ms": duration * 1000,
            "inputs": self._sanitize(inputs),
            "outputs": self._sanitize(outputs),
            "metadata": metadata or {},
            "error": error
        }
        
        self.events.append(event)
        self.logger.info(f"Node execution: {node_id}", extra=event)
        
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
    
    def log_branch_decision(
        self,
        from_node: str,
        to_node: str,
        condition: str,
        result: bool,
        context: Dict[str, Any],
        execution_id: Optional[str] = None
    ):
        """Log a branch decision"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "execution_id": execution_id,
            "type": "branch_decision",
            "from_node": from_node,
            "to_node": to_node,
            "condition": condition,
            "result": result,
            "context": self._sanitize(context)
        }
        
        self.events.append(event)
        self.logger.info(f"Branch: {from_node} → {to_node}", extra=event)
    
    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data and truncate large values"""
        sanitized = {}
        sensitive_keys = ["password", "api_key", "token", "secret"]
        
        for key, value in data.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "***"
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "..."
            elif isinstance(value, (dict, list)) and len(str(value)) > 1000:
                sanitized[key] = str(value)[:1000] + "..."
            else:
                sanitized[key] = value
        return sanitized
    
    def get_execution_trace(self, execution_id: str) -> List[Dict]:
        """Get full execution trace for an execution"""
        return [e for e in self.events if e.get("execution_id") == execution_id]
    
    def get_node_history(self, node_id: str) -> List[Dict]:
        """Get execution history for a specific node"""
        return [e for e in self.events if e.get("node_id") == node_id]


class GraphVisualizer:
    """Visualize graph structure and execution"""
    
    def __init__(self, graph: PromptGraph):
        if not VISUALIZATION_AVAILABLE:
            raise ImportError(
                "matplotlib and networkx are required for visualization. "
                "Install with: pip install matplotlib networkx"
            )
        self.graph = graph
    
    def visualize_structure(self, filepath: Optional[str] = None, show: bool = True):
        """Visualize graph structure"""
        pos = nx.spring_layout(self.graph.graph, k=2, iterations=50)
        
        plt.figure(figsize=(14, 10))
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph.graph,
            pos,
            node_color="lightblue",
            node_size=3000,
            alpha=0.9
        )
        
        # Draw edges
        nx.draw_networkx_edges(
            self.graph.graph,
            pos,
            edge_color="gray",
            arrows=True,
            arrowsize=20,
            width=2
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            self.graph.graph,
            pos,
            font_size=10,
            font_weight="bold"
        )
        
        plt.title(f"Prompt Graph: {self.graph.graph_id}", fontsize=16, fontweight="bold")
        plt.axis("off")
        
        if filepath:
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            if not show:
                plt.close()
        elif show:
            plt.show()
        else:
            plt.close()
    
    def visualize_execution(
        self,
        executor: GraphExecutor,
        filepath: Optional[str] = None,
        show: bool = True
    ):
        """Visualize graph with execution status"""
        pos = nx.spring_layout(self.graph.graph, k=2, iterations=50)
        
        plt.figure(figsize=(14, 10))
        
        # Color nodes by status
        node_colors = []
        for node_id in self.graph.graph.nodes():
            result = executor.node_results.get(node_id)
            if not result:
                node_colors.append("gray")  # Not executed
            elif result.status == NodeStatus.SUCCESS:
                node_colors.append("green")
            elif result.status == NodeStatus.FAILED:
                node_colors.append("red")
            else:
                node_colors.append("yellow")
        
        nx.draw_networkx_nodes(
            self.graph.graph,
            pos,
            node_color=node_colors,
            node_size=3000,
            alpha=0.9
        )
        
        nx.draw_networkx_edges(
            self.graph.graph,
            pos,
            edge_color="gray",
            arrows=True,
            arrowsize=20,
            width=2
        )
        
        nx.draw_networkx_labels(
            self.graph.graph,
            pos,
            font_size=10,
            font_weight="bold"
        )
        
        plt.title(f"Prompt Graph Execution: {self.graph.graph_id}", fontsize=16, fontweight="bold")
        plt.axis("off")
        
        if filepath:
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            if not show:
                plt.close()
        elif show:
            plt.show()
        else:
            plt.close()


class LineageTracker:
    """Track data lineage for audit and compliance"""
    
    def __init__(self):
        self.lineage: Dict[str, Dict] = {}
    
    def track_execution(
        self,
        execution_id: str,
        graph_version: str,
        node_versions: Dict[str, str],
        inputs: Dict[str, Any],
        outputs: Dict[str, Any]
    ):
        """Track full execution lineage"""
        self.lineage[execution_id] = {
            "graph_version": graph_version,
            "node_versions": node_versions,
            "inputs": self._sanitize(inputs),
            "outputs": self._sanitize(outputs),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_lineage(self, execution_id: str) -> Optional[Dict]:
        """Get lineage for an execution"""
        return self.lineage.get(execution_id)
    
    def find_by_output(self, output_key: str, output_value: Any) -> List[str]:
        """Find executions that produced a specific output"""
        matches = []
        for exec_id, data in self.lineage.items():
            if data["outputs"].get(output_key) == output_value:
                matches.append(exec_id)
        return matches
    
    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data"""
        sanitized = {}
        sensitive_keys = ["password", "api_key", "token", "secret"]
        
        for key, value in data.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "***"
            else:
                sanitized[key] = value
        return sanitized

