#!/usr/bin/env python3
"""Simple script to run examples"""

import sys
import os

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_example.py <example_name>")
        print("\nAvailable examples:")
        print("  - customer_support_bot")
        print("  - legal_document_assistant")
        sys.exit(1)
    
    example_name = sys.argv[1]
    
    if example_name == "customer_support_bot":
        from examples.customer_support_bot import main
        main()
    elif example_name == "legal_document_assistant":
        from examples.legal_document_assistant import main
        main()
    else:
        print(f"Unknown example: {example_name}")
        sys.exit(1)

