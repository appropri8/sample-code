"""Mesh router that routes messages between agents."""
from typing import Dict, Any, List


class MeshRouter:
    """Router that forwards messages and preserves trace context."""
    
    def __init__(self, agents: Dict[str, Any], tracer):
        self.agents = agents
        self.tracer = tracer
    
    def route(self, message: Dict[str, Any], route: List[str]) -> Dict[str, Any]:
        """Route message through agent chain, preserving trace context."""
        current_message = message
        
        for agent_name in route:
            agent = self.agents.get(agent_name)
            if not agent:
                raise ValueError(f"Agent {agent_name} not found")
            
            # Process with current agent
            # Trace context is automatically propagated via message envelope
            current_message = agent.process(current_message)
        
        return current_message

