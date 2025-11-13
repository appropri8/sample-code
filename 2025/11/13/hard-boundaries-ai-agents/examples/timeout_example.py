"""Example of timeout enforcement"""

from src.timeouts import StepBudget, StepLimitExceeded, timeout, TimeoutError
import time


def example_step_budget():
    """Example of step budget"""
    budget = StepBudget(max_steps=5)
    
    print("Step budget example:")
    for i in range(7):
        if budget.check():
            budget.use_step()
            print(f"Step {i+1}: {budget.steps_taken}/{budget.max_steps} steps used")
        else:
            print(f"Step {i+1}: Budget exceeded!")
            break


def example_timeout():
    """Example of timeout"""
    print("\nTimeout example:")
    
    def slow_operation():
        time.sleep(2)
        return "Done"
    
    try:
        with timeout(1):  # 1 second timeout
            result = slow_operation()
            print(f"Result: {result}")
    except TimeoutError as e:
        print(f"Timeout: {e}")


if __name__ == "__main__":
    example_step_budget()
    example_timeout()

