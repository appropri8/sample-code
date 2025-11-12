#!/usr/bin/env python3
"""Verify that the setup is correct"""

import sys
import os

def verify_imports():
    """Verify all imports work"""
    print("Verifying imports...")
    try:
        from src import (
            PromptGraph,
            GraphExecutor,
            PromptNode,
            RetrievalNode,
            DecisionNode,
            ToolNode,
            MemoryNode,
            TransformNode,
            ObservabilityLogger,
            GraphVisualizer,
            LineageTracker
        )
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def verify_basic_functionality():
    """Verify basic functionality works"""
    print("\nVerifying basic functionality...")
    try:
        from src import PromptGraph, RetrievalNode, ToolNode, GraphExecutor
        
        # Create a simple graph
        graph = PromptGraph("test")
        
        def mock_retrieval(query: str, top_k: int):
            return [f"Doc {i}" for i in range(top_k)]
        
        node1 = RetrievalNode(
            node_id="retrieve",
            query_field="query",
            top_k=2,
            retrieval_function=mock_retrieval
        )
        
        def process(context: str) -> str:
            return f"Processed: {context}"
        
        node2 = ToolNode(
            node_id="process",
            tool_function=process,
            inputs=["context"]
        )
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge("retrieve", "process", {"context": "context"})
        
        executor = GraphExecutor(graph)
        result = executor.execute({"query": "test"})
        
        if "result" in result:
            print("✅ Basic graph execution works")
            return True
        else:
            print(f"❌ Unexpected result: {result}")
            return False
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Prompt-Graph Setup Verification")
    print("=" * 60)
    
    checks = [
        verify_imports(),
        verify_basic_functionality()
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed! Setup is correct.")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

