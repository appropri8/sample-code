"""Agent implementation with versioning and tool management"""
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import time


class AgentRole(str, Enum):
    PLANNER = "planner"
    WORKER = "worker"
    CRITIC = "critic"
    ROUTER = "router"


class Agent:
    """Agent with explicit versioning and tool management"""
    
    def __init__(
        self,
        role: AgentRole,
        model_config: Dict[str, Any],
        tools: List[str],
        version: str,
        tool_registry: Optional[Dict[str, callable]] = None
    ):
        self.role = role
        self.model_config = model_config
        self.tools = tools
        self.version = version
        self.tool_registry = tool_registry or {}
        self.tools_called = []
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent with input data"""
        start_time = time.time()
        
        try:
            # Simulate agent execution
            result = self._execute(input_data)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "result": result,
                "tools_called": self.tools_called,
                "latency_ms": latency_ms,
                "agent_version": self.version
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "error": str(e),
                "tools_called": self.tools_called,
                "latency_ms": latency_ms,
                "agent_version": self.version
            }
    
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic"""
        # Simulate agent decision-making
        if self.role == AgentRole.PLANNER:
            return self._plan(input_data)
        elif self.role == AgentRole.WORKER:
            return self._work(input_data)
        elif self.role == AgentRole.CRITIC:
            return self._critique(input_data)
        else:
            return {"status": "unknown_role"}
    
    def _plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Planner agent logic"""
        plan = {
            "steps": [],
            "tools_needed": []
        }
        
        # Simple planning logic
        if "reset password" in input_data.get("input", "").lower():
            plan["steps"] = ["search_kb", "create_ticket"]
            plan["tools_needed"] = ["search_kb", "create_ticket"]
        
        # Track tool calls
        for tool in plan["tools_needed"]:
            if tool in self.tools:
                self.tools_called.append(tool)
        
        return {"plan": plan}
    
    def _work(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Worker agent logic"""
        tools_to_call = input_data.get("tools", [])
        results = {}
        
        for tool in tools_to_call:
            if tool in self.tools and tool in self.tool_registry:
                try:
                    result = self.tool_registry[tool](input_data)
                    results[tool] = result
                    self.tools_called.append(tool)
                except Exception as e:
                    results[tool] = {"error": str(e)}
        
        return {"results": results}
    
    def _critique(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Critic agent logic"""
        return {
            "critique": "Work looks good",
            "suggestions": []
        }

