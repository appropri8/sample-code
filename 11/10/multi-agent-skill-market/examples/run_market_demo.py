import argparse, json
from src.main import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="Generate a bullet-point summary of reflexive agents.")
    args = parser.parse_args()
    result = run(args.task)
    print(json.dumps(result, indent=2))
