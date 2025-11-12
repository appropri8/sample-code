"""Advanced multi-step workflow example"""

import uuid
import time
from src import ObservabilityLogger, InstrumentedLLM, WorkflowLogger


class AdvancedWorkflow:
    """Multi-step workflow with retrieval and tool calls"""
    
    def __init__(self):
        self.llm_logger = ObservabilityLogger()
        self.workflow_logger = WorkflowLogger()
        self.llm = InstrumentedLLM(self.llm_logger)
    
    def process_document(self, document: str):
        """Process a document through multiple steps"""
        request_id = str(uuid.uuid4())
        
        # Step 1: Extract metadata
        extract_result = self.llm.call(
            prompt=f"Extract key metadata from this document: {document[:500]}",
            model="gpt-3.5-turbo",
            prompt_version="v1"
        )
        metadata = extract_result["content"]
        
        # Step 2: Retrieve similar documents (simulated)
        start_time = time.time()
        similar_docs = self._retrieve_similar(document)
        retrieval_latency = (time.time() - start_time) * 1000
        
        self.workflow_logger.log_tool_call(
            request_id=request_id,
            tool_name="retrieve_similar",
            inputs={"document": document[:100]},
            output={"count": len(similar_docs)},
            latency_ms=retrieval_latency,
            status="success"
        )
        
        # Step 3: Generate summary
        summary_result = self.llm.call(
            prompt=f"Document: {document[:500]}\n\nSimilar documents: {len(similar_docs)}\n\nGenerate a summary.",
            model="gpt-3.5-turbo",
            prompt_version="v1"
        )
        summary = summary_result["content"]
        
        # Step 4: Check complexity
        complexity = 0.6  # Would come from analysis
        is_complex = complexity > 0.7
        
        self.workflow_logger.log_branch_decision(
            request_id=request_id,
            from_node="generate_summary",
            to_node="human_review" if is_complex else "store_result",
            condition="complexity > 0.7",
            condition_result=is_complex,
            context={"complexity": complexity}
        )
        
        if is_complex:
            # Escalate to human
            start_time = time.time()
            review_result = self._escalate_to_human(document, summary)
            review_latency = (time.time() - start_time) * 1000
            
            self.workflow_logger.log_tool_call(
                request_id=request_id,
                tool_name="human_review",
                inputs={"document": document[:100], "summary": summary[:100]},
                output=review_result,
                latency_ms=review_latency,
                status="success"
            )
            return {"summary": review_result, "reviewed": True}
        
        # Store result
        start_time = time.time()
        self._store_result(metadata, summary)
        store_latency = (time.time() - start_time) * 1000
        
        self.workflow_logger.log_tool_call(
            request_id=request_id,
            tool_name="store_result",
            inputs={"metadata": metadata[:100], "summary": summary[:100]},
            output={"stored": True},
            latency_ms=store_latency,
            status="success"
        )
        
        return {"summary": summary, "reviewed": False}
    
    def _retrieve_similar(self, document: str):
        """Simulate retrieval"""
        time.sleep(0.1)  # Simulate API call
        return ["doc1", "doc2", "doc3"]
    
    def _escalate_to_human(self, document: str, summary: str):
        """Simulate human review"""
        time.sleep(0.2)
        return f"Human-reviewed: {summary}"
    
    def _store_result(self, metadata: str, summary: str):
        """Simulate storage"""
        time.sleep(0.05)
        return True


if __name__ == "__main__":
    workflow = AdvancedWorkflow()
    
    test_document = """
    This is a sample document for processing.
    It contains multiple paragraphs and information.
    The workflow will extract metadata, retrieve similar documents,
    generate a summary, and decide whether to escalate to human review.
    """
    
    print("Processing document...")
    result = workflow.process_document(test_document)
    print(f"Summary: {result['summary'][:200]}...")
    print(f"Reviewed: {result['reviewed']}")
    print("\nWorkflow completed. Check observability.db for logs.")

