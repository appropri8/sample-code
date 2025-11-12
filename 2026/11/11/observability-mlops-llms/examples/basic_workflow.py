"""Basic workflow example with observability"""

import uuid
import time
from src import ObservabilityLogger, InstrumentedLLM, WorkflowLogger


class ObservabilityWorkflow:
    """Example workflow with full observability"""
    
    def __init__(self):
        self.llm_logger = ObservabilityLogger()
        self.workflow_logger = WorkflowLogger()
        self.llm = InstrumentedLLM(self.llm_logger)
    
    def process_request(self, user_input: str, confidence_threshold: float = 0.7):
        """Process a user request with observability"""
        request_id = str(uuid.uuid4())
        
        # Step 1: Generate response
        result = self.llm.call(
            prompt=f"Answer this question: {user_input}",
            model="gpt-3.5-turbo",
            prompt_version="v1"
        )
        
        response = result["content"]
        
        # Step 2: Check confidence (simplified - in practice, extract from response)
        confidence = 0.8  # Would come from LLM response
        
        # Step 3: Branch decision
        needs_human_review = confidence < confidence_threshold
        
        self.workflow_logger.log_branch_decision(
            request_id=request_id,
            from_node="generate_response",
            to_node="human_review" if needs_human_review else "final_response",
            condition=f"confidence < {confidence_threshold}",
            condition_result=needs_human_review,
            context={"confidence": confidence, "threshold": confidence_threshold}
        )
        
        if needs_human_review:
            # Tool call: escalate to human
            start_time = time.time()
            try:
                # Simulate human review tool
                review_result = self._escalate_to_human(user_input, response)
                latency_ms = (time.time() - start_time) * 1000
                
                self.workflow_logger.log_tool_call(
                    request_id=request_id,
                    tool_name="human_review",
                    inputs={"user_input": user_input, "response": response},
                    output=review_result,
                    latency_ms=latency_ms,
                    status="success"
                )
                
                return {"response": review_result, "reviewed": True}
            
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self.workflow_logger.log_tool_call(
                    request_id=request_id,
                    tool_name="human_review",
                    inputs={"user_input": user_input, "response": response},
                    output=None,
                    latency_ms=latency_ms,
                    status="error",
                    error=str(e)
                )
                raise
        
        return {"response": response, "reviewed": False}
    
    def _escalate_to_human(self, user_input: str, response: str):
        """Simulate human review escalation"""
        return f"Human-reviewed: {response}"


if __name__ == "__main__":
    workflow = ObservabilityWorkflow()
    
    # Process a few requests
    test_inputs = [
        "What is the capital of France?",
        "Explain quantum computing",
        "How do I reset my password?",
    ]
    
    for user_input in test_inputs:
        print(f"\nProcessing: {user_input}")
        result = workflow.process_request(user_input)
        print(f"Response: {result['response'][:100]}...")
        print(f"Reviewed: {result['reviewed']}")
    
    print("\nWorkflow completed. Check observability.db for logs.")

