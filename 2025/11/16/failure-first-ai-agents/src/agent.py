"""Failure-first agent implementation."""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from .retry_timeout import retry_with_backoff, should_retry
from .fallback_chain import ToolWithFallback, ToolError
from .human_handoff import HumanHandoff, HandoffContext

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent execution states."""
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ToolConfig:
    """Configuration for a tool."""
    name: str
    timeout: float
    max_retries: int
    requires_approval: bool = False


class FailureFirstAgent:
    """An agent designed to handle failures gracefully."""
    
    def __init__(
        self,
        tool_configs: Dict[str, ToolConfig],
        workflow_timeout: float = 300.0,
        escalation_threshold: int = 3
    ):
        self.tool_configs = tool_configs
        self.workflow_timeout = workflow_timeout
        self.escalation_threshold = escalation_threshold
        self.state = AgentState.RUNNING
        self.start_time = None
        self.error_counts = {}
        self.executed_steps = []
        self.handoff = HumanHandoff()
        self.tools = {}  # Store tool instances
    
    def register_tool(self, name: str, tool: ToolWithFallback):
        """Register a tool with the agent."""
        self.tools[name] = tool
    
    async def run(self, user_input: str, plan: List[Dict]) -> Dict:
        """Run the agent workflow."""
        self.start_time = time.time()
        self.state = AgentState.RUNNING
        self.executed_steps = []
        
        try:
            for step in plan:
                # Check workflow timeout
                if self._workflow_timed_out():
                    return await self._handle_timeout(user_input, plan)
                
                # Execute step
                result = await self._execute_step(step, user_input, plan)
                
                if result.get("requires_approval"):
                    self.state = AgentState.WAITING_APPROVAL
                    return result
                
                if result.get("escalated"):
                    self.state = AgentState.ESCALATED
                    return result
                
                self.executed_steps.append({
                    "step": step,
                    "result": result,
                    "timestamp": time.time()
                })
            
            self.state = AgentState.COMPLETED
            return {
                "status": "completed",
                "result": "Workflow completed successfully",
                "steps_executed": len(self.executed_steps)
            }
        
        except Exception as e:
            self.state = AgentState.FAILED
            return await self._handle_error(e, user_input, plan)
    
    async def _execute_step(self, step: Dict, user_input: str, plan: List[Dict]) -> Dict:
        """Execute a single step with failure handling."""
        tool_name = step.get("tool")
        tool_config = self.tool_configs.get(tool_name)
        
        if not tool_config:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Check if approval needed
        if tool_config.requires_approval:
            action = {
                "type": tool_name,
                "params": step.get("params", {})
            }
            context = HandoffContext(
                user_input=user_input,
                plan={"steps": plan},
                executed_steps=self.executed_steps,
                failing_step=None,
                error=None
            )
            approval_result = await self.handoff.ask_before_act(action, context)
            
            if approval_result.get("status") == "cancelled":
                return {
                    "status": "cancelled",
                    "requires_approval": True,
                    "message": "Action not approved"
                }
        
        # Execute with retry and timeout
        return await self._call_tool_with_retry(
            tool_name,
            tool_config,
            step.get("params", {})
        )
    
    async def _call_tool_with_retry(
        self,
        tool_name: str,
        config: ToolConfig,
        params: Dict
    ) -> Dict:
        """Call tool with retry and timeout."""
        last_error = None
        
        for attempt in range(config.max_retries):
            try:
                # Call tool with timeout
                if tool_name in self.tools:
                    result = await asyncio.wait_for(
                        self.tools[tool_name].call(params),
                        timeout=config.timeout
                    )
                else:
                    # Fallback to simple tool call
                    result = await asyncio.wait_for(
                        self._call_tool(tool_name, params),
                        timeout=config.timeout
                    )
                
                # Success - reset error count
                error_key = f"{tool_name}:success"
                self.error_counts[error_key] = 0
                
                return {
                    "status": "success",
                    "result": result,
                    "attempts": attempt + 1
                }
            
            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"Tool {tool_name} timed out (attempt {attempt + 1})")
                
                # Check if should escalate
                if await self._should_escalate(tool_name, e):
                    return await self._escalate(e, tool_name, params)
            
            except ToolError as e:
                last_error = e
                logger.warning(f"Tool {tool_name} failed: {e} (attempt {attempt + 1})")
                
                # Don't retry certain errors
                if not should_retry(e):
                    raise
                
                # Check if should escalate
                if await self._should_escalate(tool_name, e):
                    return await self._escalate(e, tool_name, params)
            
            except Exception as e:
                last_error = e
                logger.warning(f"Tool {tool_name} failed: {e} (attempt {attempt + 1})")
                
                # Don't retry certain errors
                if not should_retry(e):
                    raise
                
                # Check if should escalate
                if await self._should_escalate(tool_name, e):
                    return await self._escalate(e, tool_name, params)
            
            # Wait before retry
            if attempt < config.max_retries - 1:
                delay = min(1.0 * (2 ** attempt), 60.0)
                await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_error
    
    async def _call_tool(self, tool_name: str, params: Dict) -> Any:
        """Call a tool (placeholder implementation)."""
        # Simulate tool call
        await asyncio.sleep(0.1)
        return {
            "tool": tool_name,
            "result": f"Result from {tool_name}",
            "params": params
        }
    
    async def _should_escalate(self, tool_name: str, error: Exception) -> bool:
        """Check if error should be escalated."""
        error_key = f"{tool_name}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        return self.error_counts[error_key] >= self.escalation_threshold
    
    async def _escalate(self, error: Exception, tool_name: str, params: Dict) -> Dict:
        """Escalate to human."""
        logger.error(f"Escalating error: {error} for tool {tool_name}")
        
        # Package context
        context = HandoffContext(
            user_input="",  # Will be set by caller
            plan={"tool": tool_name, "params": params},
            executed_steps=self.executed_steps,
            failing_step={"tool": tool_name, "params": params},
            error=error
        )
        
        # Escalate
        result = await self.handoff.stop_and_escalate(error, context)
        
        return {
            "status": "escalated",
            "escalated": True,
            **result
        }
    
    def _workflow_timed_out(self) -> bool:
        """Check if workflow has timed out."""
        if not self.start_time:
            return False
        elapsed = time.time() - self.start_time
        return elapsed >= self.workflow_timeout
    
    async def _handle_timeout(self, user_input: str, plan: List[Dict]) -> Dict:
        """Handle workflow timeout."""
        logger.warning("Workflow timed out")
        return {
            "status": "timeout",
            "message": "Workflow exceeded time limit",
            "steps_executed": len(self.executed_steps),
            "steps_remaining": len(plan) - len(self.executed_steps)
        }
    
    async def _handle_error(self, error: Exception, user_input: str, plan: List[Dict]) -> Dict:
        """Handle workflow error."""
        logger.error(f"Workflow failed: {error}")
        return {
            "status": "failed",
            "error": str(error),
            "error_type": type(error).__name__,
            "steps_executed": len(self.executed_steps),
            "context": {
                "user_input": user_input,
                "plan": plan,
                "executed_steps": self.executed_steps
            }
        }

