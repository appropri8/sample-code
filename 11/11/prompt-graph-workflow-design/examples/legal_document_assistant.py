"""Example: Enterprise Legal Document Assistant using Prompt-Graph"""

import os
import sys
import json
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


def store_legal_summary(summary: str, metadata: dict) -> dict:
    """Tool function to store legal summary"""
    print(f"\n[STORAGE] Storing summary for document: {metadata.get('document_type', 'Unknown')}")
    print(f"[STORAGE] Summary length: {len(summary)} characters")
    return {
        "stored": True,
        "document_id": f"DOC-{hash(str(metadata)) % 100000}",
        "timestamp": "2025-11-11T12:00:00Z"
    }


def escalate_to_lawyer(document: str, summary: str, metadata: dict) -> dict:
    """Tool function to escalate to human lawyer"""
    print(f"\n[ESCALATION] Escalating to legal team")
    print(f"[ESCALATION] Document Type: {metadata.get('document_type', 'Unknown')}")
    print(f"[ESCALATION] Summary preview: {summary[:200]}...")
    return {
        "escalated": True,
        "lawyer_review_id": f"LAW-{hash(document) % 100000}",
        "priority": "high" if metadata.get('complexity_score', 0) > 0.8 else "medium"
    }


def create_legal_assistant_graph():
    """Create the legal document assistant graph"""
    graph = PromptGraph("legal_document_assistant")
    
    # Mock retrieval function
    def mock_legal_retrieval(document: str, top_k: int) -> list:
        """Mock retrieval of similar legal cases"""
        similar_cases = [
            "Case XYZ-2024: Similar contract dispute resolved through mediation",
            "Case ABC-2023: Precedent set for intellectual property rights",
            "Case DEF-2024: Regulatory compliance requirements for data privacy"
        ]
        return similar_cases[:top_k]
    
    # Nodes
    extract_metadata = PromptNode(
        node_id="extract_metadata",
        prompt_template="""Extract metadata from this legal document:
{document}

Return JSON with: date, parties, document_type, jurisdiction, key_topics

Example format:
{{
    "date": "2025-01-15",
    "parties": ["Party A", "Party B"],
    "document_type": "contract",
    "jurisdiction": "US",
    "key_topics": ["intellectual property", "licensing"]
}}""",
        inputs=["document"],
        outputs=["metadata"],
        model="gpt-3.5-turbo"
    )
    
    retrieve_cases = RetrievalNode(
        node_id="retrieve_similar_cases",
        query_field="document",
        top_k=5,
        retrieval_function=mock_legal_retrieval
    )
    
    generate_summary = PromptNode(
        node_id="generate_summary",
        prompt_template="""Legal Document: {document}

Similar Cases: {similar_cases}

Metadata: {metadata}

Generate a comprehensive legal summary focusing on:
- Key legal issues
- Relevant precedents
- Risk assessment
- Recommended actions

Also provide:
- confidence: 0.0 to 1.0 (how confident you are in the summary)
- complexity_score: 0.0 to 1.0 (how complex the document is)

Return as JSON:
{{
    "summary": "detailed summary here",
    "confidence": 0.85,
    "complexity_score": 0.7,
    "key_issues": ["issue1", "issue2"],
    "risk_level": "medium"
}}""",
        inputs=["document", "similar_cases", "metadata"],
        outputs=["summary", "confidence", "complexity_score"],
        model="gpt-3.5-turbo"
    )
    
    check_confidence = DecisionNode(
        node_id="check_confidence",
        condition="confidence < 0.7",
        true_branch="human_review",
        false_branch="check_complexity",
        inputs=["confidence"]
    )
    
    check_complexity = DecisionNode(
        node_id="check_complexity",
        condition="complexity_score > 0.8",
        true_branch="human_review",
        false_branch="format_response",
        inputs=["complexity_score"]
    )
    
    format_response = PromptNode(
        node_id="format_response",
        prompt_template="""Format this legal summary for storage in our system:

Summary: {summary}
Metadata: {metadata}

Create a well-structured, professional format suitable for legal records.""",
        inputs=["summary", "metadata"],
        outputs=["formatted_summary"],
        model="gpt-3.5-turbo"
    )
    
    store_result = ToolNode(
        node_id="store_result",
        tool_function=store_legal_summary,
        inputs=["formatted_summary", "metadata"]
    )
    
    human_review = ToolNode(
        node_id="human_review",
        tool_function=escalate_to_lawyer,
        inputs=["document", "summary", "metadata"]
    )
    
    # Add nodes
    for node in [extract_metadata, retrieve_cases, generate_summary, 
                 check_confidence, check_complexity, format_response, 
                 store_result, human_review]:
        graph.add_node(node)
    
    # Add edges
    graph.add_edge("extract_metadata", "retrieve_similar_cases", {
        "document": "document"
    })
    
    graph.add_edge("retrieve_similar_cases", "generate_summary", {
        "similar_cases": "similar_cases",
        "document": "document"
    })
    
    graph.add_edge("extract_metadata", "generate_summary", {
        "metadata": "metadata"
    })
    
    graph.add_edge("generate_summary", "check_confidence", {
        "confidence": "confidence"
    })
    
    graph.add_edge("check_confidence", "check_complexity", 
                   condition="confidence >= 0.7")
    
    graph.add_edge("check_confidence", "human_review",
                   condition="confidence < 0.7")
    
    graph.add_edge("check_complexity", "format_response",
                   condition="complexity_score <= 0.8")
    
    graph.add_edge("check_complexity", "human_review",
                   condition="complexity_score > 0.8")
    
    graph.add_edge("format_response", "store_result", {
        "formatted_summary": "formatted_summary",
        "metadata": "metadata"
    })
    
    graph.add_edge("generate_summary", "human_review", {
        "document": "document",
        "summary": "summary",
        "metadata": "metadata"
    }, condition="routed_to_human")
    
    return graph


def main():
    """Run the legal document assistant example"""
    print("=" * 60)
    print("Legal Document Assistant - Prompt-Graph Example")
    print("=" * 60)
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  Warning: OPENAI_API_KEY not set. Using mock responses.")
        print("   Set OPENAI_API_KEY environment variable to use real LLM calls.\n")
    
    # Create graph
    graph = create_legal_assistant_graph()
    
    # Set up logging
    logger = ObservabilityLogger()
    
    # Create executor
    executor = GraphExecutor(graph, logger=logger)
    
    # Example legal document
    sample_document = """
    SOFTWARE LICENSE AGREEMENT
    
    This Software License Agreement ("Agreement") is entered into on January 15, 2025,
    between TechCorp Inc. ("Licensor") and DataSystems LLC ("Licensee").
    
    WHEREAS, Licensor owns certain proprietary software;
    WHEREAS, Licensee desires to license such software;
    
    NOW THEREFORE, the parties agree as follows:
    
    1. GRANT OF LICENSE
    Licensor grants Licensee a non-exclusive, non-transferable license to use the Software.
    
    2. INTELLECTUAL PROPERTY
    All rights, title, and interest in the Software remain with Licensor.
    
    3. TERM AND TERMINATION
    This Agreement shall commence on the Effective Date and continue for a period of three years.
    """
    
    print(f"\nProcessing legal document...")
    print(f"Document preview: {sample_document[:100]}...\n")
    
    try:
        result = executor.execute({
            "document": sample_document
        })
        
        print("\n" + "=" * 60)
        print("EXECUTION RESULTS")
        print("=" * 60)
        
        if "formatted_summary" in result:
            print("\n✅ Summary Generated and Stored:")
            print(f"Document ID: {result.get('document_id', 'N/A')}")
            print(f"\nSummary:\n{result.get('formatted_summary', 'N/A')}")
        elif "escalated" in result:
            print("\n⚠️  Escalated to Human Lawyer Review")
            print(f"Review ID: {result.get('lawyer_review_id', 'N/A')}")
            print(f"Priority: {result.get('priority', 'N/A')}")
        else:
            print(f"\n📋 Full Result:")
            print(json.dumps(result, indent=2))
        
        # Show execution trace
        print("\n" + "=" * 60)
        print("EXECUTION TRACE")
        print("=" * 60)
        for node_id, node_result in executor.node_results.items():
            status_icon = "✅" if node_result.status.value == "success" else "❌"
            print(f"{status_icon} {node_id}: {node_result.status.value}")
            if node_result.metadata:
                print(f"   Metadata: {node_result.metadata}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Execution complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

