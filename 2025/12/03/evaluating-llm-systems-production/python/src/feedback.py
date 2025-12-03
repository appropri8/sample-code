"""
Feedback capture module.
Handles explicit feedback (thumbs up/down, ratings) and implicit signals.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ExplicitFeedback:
    """Explicit user feedback."""
    request_id: str
    thumbs_up: Optional[bool] = None
    rating: Optional[int] = None  # 1-5 scale
    labels: Optional[Dict[str, str]] = None  # e.g., {"correctness": "correct", "helpfulness": "helpful"}
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class ImplicitSignal:
    """Implicit signal from user behavior."""
    request_id: str
    signal_type: str  # "edit", "abandon", "repeat_query", "click_through", "time_spent"
    value: Optional[float] = None  # For quantitative signals like time_spent
    metadata: Optional[Dict] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class FeedbackCollector:
    """Collects explicit and implicit feedback."""
    
    def __init__(self, feedback_file: Optional[str] = None):
        self.feedback_file = feedback_file
        self.explicit_feedback: List[ExplicitFeedback] = []
        self.implicit_signals: List[ImplicitSignal] = []
    
    def record_thumbs_up(self, request_id: str, thumbs_up: bool):
        """Record thumbs up/down feedback."""
        feedback = ExplicitFeedback(
            request_id=request_id,
            thumbs_up=thumbs_up
        )
        self.explicit_feedback.append(feedback)
        self._save_feedback(feedback)
        return feedback
    
    def record_rating(self, request_id: str, rating: int):
        """Record rating (1-5 scale)."""
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        feedback = ExplicitFeedback(
            request_id=request_id,
            rating=rating
        )
        self.explicit_feedback.append(feedback)
        self._save_feedback(feedback)
        return feedback
    
    def record_labels(self, request_id: str, labels: Dict[str, str]):
        """Record task-specific labels."""
        feedback = ExplicitFeedback(
            request_id=request_id,
            labels=labels
        )
        self.explicit_feedback.append(feedback)
        self._save_feedback(feedback)
        return feedback
    
    def record_implicit_signal(
        self,
        request_id: str,
        signal_type: str,
        value: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """Record an implicit signal."""
        signal = ImplicitSignal(
            request_id=request_id,
            signal_type=signal_type,
            value=value,
            metadata=metadata or {}
        )
        self.implicit_signals.append(signal)
        self._save_signal(signal)
        return signal
    
    def record_edit(self, request_id: str, edit_ratio: float):
        """Record that user edited the output (edit_ratio: 0-1, how much was edited)."""
        return self.record_implicit_signal(
            request_id=request_id,
            signal_type="edit",
            value=edit_ratio,
            metadata={"high_edit": edit_ratio > 0.5}
        )
    
    def record_abandon(self, request_id: str):
        """Record that user abandoned the flow."""
        return self.record_implicit_signal(
            request_id=request_id,
            signal_type="abandon"
        )
    
    def record_repeat_query(self, request_id: str, original_request_id: str):
        """Record that user repeated the same query."""
        return self.record_implicit_signal(
            request_id=request_id,
            signal_type="repeat_query",
            metadata={"original_request_id": original_request_id}
        )
    
    def record_time_spent(self, request_id: str, seconds: float):
        """Record time user spent on the response."""
        return self.record_implicit_signal(
            request_id=request_id,
            signal_type="time_spent",
            value=seconds
        )
    
    def _save_feedback(self, feedback: ExplicitFeedback):
        """Save feedback to file if specified."""
        if self.feedback_file:
            with open(self.feedback_file, 'a') as f:
                f.write(json.dumps({
                    "type": "explicit",
                    "request_id": feedback.request_id,
                    "thumbs_up": feedback.thumbs_up,
                    "rating": feedback.rating,
                    "labels": feedback.labels,
                    "timestamp": feedback.timestamp
                }) + '\n')
    
    def _save_signal(self, signal: ImplicitSignal):
        """Save signal to file if specified."""
        if self.feedback_file:
            with open(self.feedback_file, 'a') as f:
                f.write(json.dumps({
                    "type": "implicit",
                    "request_id": signal.request_id,
                    "signal_type": signal.signal_type,
                    "value": signal.value,
                    "metadata": signal.metadata,
                    "timestamp": signal.timestamp
                }) + '\n')
    
    def get_feedback_stats(self, request_ids: Optional[List[str]] = None) -> Dict:
        """Get feedback statistics."""
        feedbacks = self.explicit_feedback
        if request_ids:
            feedbacks = [f for f in feedbacks if f.request_id in request_ids]
        
        stats = {
            "total": len(feedbacks),
            "thumbs_up_count": sum(1 for f in feedbacks if f.thumbs_up is True),
            "thumbs_down_count": sum(1 for f in feedbacks if f.thumbs_up is False),
            "avg_rating": None,
            "label_counts": {}
        }
        
        ratings = [f.rating for f in feedbacks if f.rating is not None]
        if ratings:
            stats["avg_rating"] = sum(ratings) / len(ratings)
        
        # Count labels
        for feedback in feedbacks:
            if feedback.labels:
                for key, value in feedback.labels.items():
                    if key not in stats["label_counts"]:
                        stats["label_counts"][key] = {}
                    stats["label_counts"][key][value] = stats["label_counts"][key].get(value, 0) + 1
        
        return stats

