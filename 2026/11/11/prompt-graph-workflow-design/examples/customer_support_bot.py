"""Example: Customer Support Bot using Prompt-Graph"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import (
    PromptGraph,
    GraphExecutor,
    PromptNode,
    RetrievalNode,
    DecisionNode,
    ToolNode,
    ObservabilityLogger
)


def escalate_to_human(question: str, answer: str) -> dict:
    """Tool function to escalate to human review"""
    print(f"\n[ESCALATION] Question: {question}")
    print(f"[ESCALATION] Generated Answer: {answer}")
    print("[ESCALATION] Escalating to human agent...")
    return {
        "escalated": True,
        "review_id": f"REV-{hash(question) % 10000}",
        "status": "pending_human_review"
    }


def create_customer_support_graph():
    """Create the customer support bot graph"""
    graph = PromptGraph("customer_support_bot")
    
    # Mock retrieval function (in production, use real vector store)
    def mock_retrieval(query: str, top_k: int) -> list:
        """Mock retrieval for demonstration"""
        faq_docs = [
            "To reset your password, go to Settings > Security > Reset Password",
            "Our refund policy allows returns within 30 days of purchase",
            "Shipping typically takes 3-5 business days",
            "You can contact support via email at support@example.com"
        ]
        # Simple keyword matching
        results = [doc for doc in faq_docs if any(word.lower() in doc.lower() for word in query.split())]
        return results[:top_k] if results else faq_docs[:2]
    
    # Define nodes
    retrieve_node = RetrievalNode(
        node_id="retrieve_faq",
        query_field="user_question",
        top_k=3,
        retrieval_function=mock_retrieval
    )
    
    prompt_node = PromptNode(
        node_id="generate_answer",
        prompt_template="""Context from FAQ: {context}

User Question: {user_question}

Generate a helpful answer based on the context. Also provide a confidence score between 0 and 1.

Format your response as JSON:
{{
    "answer": "your answer here",
    "confidence": 0.85
}}""",
        inputs=["context", "user_question"],
        outputs=["answer", "confidence"],
        model="gpt-3.5-turbo"  # Use cheaper model for demo
    )
    
    decision_node = DecisionNode(
        node_id="check_confidence",
        condition="confidence < 0.7",
        true_branch="human_review",
        false_branch="format_response",
        inputs=["confidence"]
    )
    
    format_node = PromptNode(
        node_id="format_response",
        prompt_template="Format this answer in a friendly, professional tone: {answer}",
        inputs=["answer"],
        outputs=["formatted_answer"],
        model="gpt-3.5-turbo"
    )
    
    human_node = ToolNode(
        node_id="human_review",
        tool_function=escalate_to_human,
        inputs=["user_question", "answer"]
    )
    
    # Add nodes
    graph.add_node(retrieve_node)
    graph.add_node(prompt_node)
    graph.add_node(decision_node)
    graph.add_node(format_node)
    graph.add_node(human_node)
    
    # Add edges
    graph.add_edge("retrieve_faq", "generate_answer", {
        "context": "context",
        "user_question": "user_question"
    })
    
    graph.add_edge("generate_answer", "check_confidence", {
        "confidence": "confidence"
    })
    
    graph.add_edge("check_confidence", "format_response", condition="confidence >= 0.7")
    graph.add_edge("check_confidence", "human_review", condition="confidence < 0.7")
    
    return graph


def main():
    """Run the customer support bot example"""
    print("=" * 60)
    print("Customer Support Bot - Prompt-Graph Example")
    print("=" * 60)
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  Warning: OPENAI_API_KEY not set. Using mock responses.")
        print("   Set OPENAI_API_KEY environment variable to use real LLM calls.\n")
    
    # Create graph
    graph = create_customer_support_graph()
    
    # Set up logging
    logger = ObservabilityLogger()
    
    # Create executor
    executor = GraphExecutor(graph, logger=logger)
    
    # Example questions
    questions = [
        "How do I reset my password?",
        "What is your return policy?",
        "Tell me about quantum computing"  # Low confidence expected
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print('='*60)
        
        try:
            result = executor.execute({
                "user_question": question
            })
            
            if "formatted_answer" in result:
                print(f"\n✅ Answer (High Confidence):")
                print(result["formatted_answer"])
            elif "escalated" in result:
                print(f"\n⚠️  Escalated to Human Review")
                print(f"Review ID: {result.get('review_id', 'N/A')}")
            else:
                print(f"\n📋 Result: {result}")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Execution complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

