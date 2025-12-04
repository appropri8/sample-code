"""
Example: Using cost limits to prevent budget overruns.
"""

from src.guardrails import CostLimiter, load_config
import yaml


def main():
    # Load cost limits configuration
    config = {
        "agents": {
            "ops-agent": {
                "daily_budget_usd": 100.0,
                "per_request_max_usd": 1.0,
                "per_tool_limits": {
                    "scale_deployment": {
                        "max_calls_per_hour": 10,
                        "cost_per_call_usd": 0.01
                    },
                    "delete_namespace": {
                        "max_calls_per_day": 1,
                        "cost_per_call_usd": 0.0
                    }
                }
            },
            "observer-agent": {
                "daily_budget_usd": 10.0,
                "per_request_max_usd": 0.1,
                "per_tool_limits": {
                    "get_metrics": {
                        "max_calls_per_minute": 60,
                        "cost_per_call_usd": 0.001
                    }
                }
            }
        },
        "alerts": {
            "budget_threshold_percent": 80,
            "cost_anomaly_multiplier": 3.0
        }
    }
    
    cost_limiter = CostLimiter(config)
    
    print("Cost Limits Example")
    print("=" * 50)
    print()
    
    # Example 1: Check budget before action
    print("Example 1: Checking budget before action")
    allowed, reason = cost_limiter.check_budget(
        agent_name="ops-agent",
        tool_name="scale_deployment",
        estimated_cost=0.01
    )
    
    if allowed:
        print(f"✅ Budget check passed: {reason}")
        # Execute tool...
        cost_limiter.record_cost(
            agent_name="ops-agent",
            tool_name="scale_deployment",
            actual_cost=0.01
        )
        print("✅ Cost recorded")
    else:
        print(f"❌ Budget check failed: {reason}")
    
    print()
    
    # Example 2: Check daily budget
    print("Example 2: Checking daily budget status")
    # Simulate multiple calls
    for i in range(5):
        allowed, reason = cost_limiter.check_budget(
            agent_name="ops-agent",
            tool_name="scale_deployment",
            estimated_cost=0.01
        )
        if allowed:
            cost_limiter.record_cost(
                agent_name="ops-agent",
                tool_name="scale_deployment",
                actual_cost=0.01
            )
            print(f"Call {i+1}: ✅ Allowed and recorded")
        else:
            print(f"Call {i+1}: ❌ {reason}")
            break
    
    print()
    
    # Example 3: Rate limiting
    print("Example 3: Rate limiting (max calls per hour)")
    # Simulate rapid calls
    for i in range(12):  # More than max_calls_per_hour (10)
        allowed, reason = cost_limiter.check_budget(
            agent_name="ops-agent",
            tool_name="scale_deployment",
            estimated_cost=0.01
        )
        if allowed:
            cost_limiter.record_cost(
                agent_name="ops-agent",
                tool_name="scale_deployment",
                actual_cost=0.01
            )
            print(f"Call {i+1}: ✅ Allowed")
        else:
            print(f"Call {i+1}: ❌ {reason}")
            break
    
    print()
    print("Note: In production, cost limits would be enforced across")
    print("all agent instances and persisted to a shared store (Redis, DB, etc.)")


if __name__ == "__main__":
    main()
