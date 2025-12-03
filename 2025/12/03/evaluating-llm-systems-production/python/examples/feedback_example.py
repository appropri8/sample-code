"""
Example: Collecting explicit and implicit feedback.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.feedback import FeedbackCollector
import uuid


def main():
    # Initialize feedback collector
    collector = FeedbackCollector(feedback_file="feedback.jsonl")
    
    # Simulate some requests
    request_ids = [str(uuid.uuid4()) for _ in range(5)]
    
    # Record explicit feedback
    print("Recording explicit feedback...")
    collector.record_thumbs_up(request_ids[0], True)
    collector.record_thumbs_up(request_ids[1], False)
    collector.record_rating(request_ids[2], 5)
    collector.record_rating(request_ids[3], 3)
    collector.record_labels(
        request_ids[4],
        {"correctness": "correct", "helpfulness": "helpful"}
    )
    
    # Record implicit signals
    print("Recording implicit signals...")
    collector.record_edit(request_ids[0], edit_ratio=0.2)  # Low edit = good
    collector.record_edit(request_ids[1], edit_ratio=0.8)  # High edit = bad
    collector.record_abandon(request_ids[2])
    collector.record_repeat_query(request_ids[3], original_request_id=request_ids[0])
    collector.record_time_spent(request_ids[4], seconds=45.5)
    
    # Get feedback stats
    print("\nFeedback Statistics:")
    stats = collector.get_feedback_stats()
    print(f"  Total feedback: {stats['total']}")
    print(f"  Thumbs up: {stats['thumbs_up_count']}")
    print(f"  Thumbs down: {stats['thumbs_down_count']}")
    print(f"  Average rating: {stats['avg_rating']}")
    print(f"  Label counts: {stats['label_counts']}")
    
    print(f"\nTotal implicit signals: {len(collector.implicit_signals)}")


if __name__ == "__main__":
    main()

