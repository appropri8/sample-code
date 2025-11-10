import argparse
from src.main import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="Summarize reflexive agents.")
    parser.add_argument("--context", type=str, default=None)
    args = parser.parse_args()

    result = run(args.task, args.context)
    print("\n=== ANSWER ===\n", result["answer"])
    print("\n=== CRITIQUE ===\n", result["critique"])
    print("\n=== SCORE ===\n", result["score"])
    print("\n=== POLICY HINT ===\n", result["hint"])
