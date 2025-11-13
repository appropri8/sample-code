"""Bounded agent wrapper that enforces all limits"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from .contracts import AgentContract
from .timeouts import StepBudget, StepLimitExceeded, call_tool_with_timeout, TimeoutError
from .budgets import TokenBudget, CostBudget, TokenBudgetExceeded, CostBudgetExceeded
from .permissions import get_tools_for_role, get_tools_for_env, log_tool_call
from .data_boundaries import prepare_safe_input


class BoundedAgent:
    """Agent with all boundaries enforced"""
    
    def __init__(
        self,
        agent_core,  # Your agent implementation
        contract: AgentContract,
        user_context: dict
    ):
        self.agent_core = agent_core
        self.contract = contract
        self.user_context = user_context
        
        # Initialize budgets
        self.step_budget = StepBudget(contract.max_steps)
        self.token_budget = TokenBudget(contract.max_tokens)
        self.cost_budget = CostBudget(contract.max_cost_dollars)
        self.start_time = time.time()
        
        # Filter tools by permissions
        self.available_tools = self._filter_tools()
        
        # Log contract
        self._log_contract()
    
    def _filter_tools(self) -> List[str]:
        """Filter tools based on permissions"""
        role = self.user_context.get("role", "user")
        env = self.user_context.get("environment", "production")
        
        # Get tools for role and environment
        role_tools = get_tools_for_role(role)
        env_tools = get_tools_for_env(env)
        
        # Intersection: must be in both
        allowed = set(role_tools) & set(env_tools)
        
        # Also check contract
        allowed = allowed & set(self.contract.allowed_tools)
        
        return list(allowed)
    
    def _log_contract(self):
        """Log the contract for this request"""
        request_id = self.user_context.get("request_id", "unknown")
        log_entry = {
            "request_id": request_id,
            "agent_name": self.contract.name,
            "allowed_tools": self.contract.allowed_tools,
            "limits": {
                "max_runtime_seconds": self.contract.max_runtime_seconds,
                "max_steps": self.contract.max_steps,
                "max_tokens": self.contract.max_tokens,
                "max_cost_dollars": self.contract.max_cost_dollars
            }
        }
        print(f"CONTRACT: {json.dumps(log_entry)}")
    
    def _check_timeout(self):
        """Check if runtime limit exceeded"""
        elapsed = time.time() - self.start_time
        if elapsed > self.contract.max_runtime_seconds:
            raise TimeoutError(f"Runtime limit exceeded: {elapsed:.2f}s")
    
    def _check_budgets(self):
        """Check if any budget exceeded"""
        if not self.step_budget.check():
            raise StepLimitExceeded("Step limit exceeded")
        
        if self.token_budget.remaining() < 100:
            raise TokenBudgetExceeded("Token budget nearly exhausted")
        
        if self.cost_budget.remaining() < 0.01:
            raise CostBudgetExceeded("Cost budget nearly exhausted")
    
    def run(self, user_input: str) -> Dict[str, Any]:
        """Run agent with all boundaries enforced"""
        request_id = self.user_context.get("request_id", f"req_{int(time.time())}")
        
        try:
            # Prepare safe input
            safe_input = prepare_safe_input(user_input, self.user_context.get("context", {}))
            
            # Run agent loop
            results = []
            
            while True:
                # Check limits
                self._check_timeout()
                self._check_budgets()
                
                if not self.step_budget.check():
                    break
                
                # Agent chooses tool
                tool_choice = self.agent_core.choose_tool(safe_input, self.available_tools)
                
                if tool_choice is None:
                    # Agent is done
                    break
                
                tool_name = tool_choice["name"]
                tool_params = tool_choice["params"]
                
                # Validate tool permission
                if tool_name not in self.available_tools:
                    return {
                        "error": f"Tool {tool_name} not allowed",
                        "request_id": request_id,
                        "partial": True,
                        "results": results
                    }
                
                # Use step
                self.step_budget.use_step()
                
                # Call tool with timeout
                try:
                    tool_result = call_tool_with_timeout(tool_name, tool_params, timeout_seconds=5)
                except TimeoutError:
                    tool_result = {"error": f"Tool {tool_name} timed out"}
                
                # Log tool call
                log_tool_call(tool_name, tool_params, self.user_context)
                
                results.append({
                    "tool": tool_name,
                    "result": tool_result
                })
                
                # Update agent
                self.agent_core.update(tool_result)
                
                # Check if done
                if self.agent_core.is_done():
                    break
            
            # Generate final response
            final_response = self.agent_core.generate_response()
            
            # Log final response
            self._log_response(request_id, final_response, results)
            
            return {
                "response": final_response,
                "request_id": request_id,
                "complete": True,
                "results": results,
                "budgets": {
                    "steps_used": self.step_budget.steps_taken,
                    "tokens_used": self.token_budget.tokens_used,
                    "cost_used": self.cost_budget.cost_used
                }
            }
            
        except TimeoutError as e:
            return self._handle_error("timeout", str(e), results, request_id)
        except StepLimitExceeded as e:
            return self._handle_error("step_limit", str(e), results, request_id)
        except TokenBudgetExceeded as e:
            return self._handle_error("token_budget", str(e), results, request_id)
        except CostBudgetExceeded as e:
            return self._handle_error("cost_budget", str(e), results, request_id)
        except Exception as e:
            return self._handle_error("unknown", str(e), results, request_id)
    
    def _handle_error(self, error_type: str, error_msg: str, results: list, request_id: str):
        """Handle errors gracefully"""
        self._log_error(request_id, error_type, error_msg)
        
        return {
            "error": error_msg,
            "error_type": error_type,
            "request_id": request_id,
            "partial": True,
            "results": results,
            "budgets": {
                "steps_used": self.step_budget.steps_taken,
                "tokens_used": self.token_budget.tokens_used,
                "cost_used": self.cost_budget.cost_used
            }
        }
    
    def _log_response(self, request_id: str, response: str, results: list):
        """Log final response"""
        log_entry = {
            "request_id": request_id,
            "response": response,
            "results_count": len(results),
            "budgets": {
                "steps_used": self.step_budget.steps_taken,
                "tokens_used": self.token_budget.tokens_used,
                "cost_used": self.cost_budget.cost_used
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"RESPONSE: {json.dumps(log_entry)}")
    
    def _log_error(self, request_id: str, error_type: str, error_msg: str):
        """Log error"""
        log_entry = {
            "request_id": request_id,
            "error_type": error_type,
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"ERROR: {json.dumps(log_entry)}")


# Simple agent core for examples
class SimpleAgentCore:
    """Simple agent core for demonstration"""
    def __init__(self):
        self.tool_results = []
        self.done = False
    
    def choose_tool(self, input_text: str, available_tools: List[str]) -> Optional[Dict[str, Any]]:
        """Choose a tool to call"""
        if self.done or len(self.tool_results) >= 3:
            return None
        
        # Simple logic: pick first available tool
        if available_tools:
            return {
                "name": available_tools[0],
                "params": {"query": input_text}
            }
        return None
    
    def update(self, tool_result: Dict[str, Any]):
        """Update agent state with tool result"""
        self.tool_results.append(tool_result)
        # Mark done after a few results
        if len(self.tool_results) >= 2:
            self.done = True
    
    def is_done(self) -> bool:
        """Check if agent is done"""
        return self.done
    
    def generate_response(self) -> str:
        """Generate final response"""
        return f"Processed {len(self.tool_results)} tools successfully."

