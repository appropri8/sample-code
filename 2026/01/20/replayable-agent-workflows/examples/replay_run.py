"""Replay a recorded run."""
import sys
import argparse
sys.path.insert(0, '.')

from src.agent import replay_run
from src.checkpoint_store import CheckpointStore


def main():
    parser = argparse.ArgumentParser(description="Replay a recorded agent run")
    parser.add_argument("--run-id", required=True, help="Run ID to replay")
    args = parser.parse_args()
    
    # Setup
    checkpoint_store = CheckpointStore()
    
    # Replay
    print(f"Replaying run: {args.run_id}")
    print()
    
    events = replay_run(args.run_id, checkpoint_store)
    
    print()
    print(f"Replay completed! ({len(events)} steps)")


if __name__ == "__main__":
    main()
