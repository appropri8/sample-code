"""Human review flagging for high-risk requests"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

class HumanReviewFlag:
    """Flag requests for human review"""
    
    def __init__(self, risk_threshold: float = 0.7):
        """
        Initialize human review flag
        
        Args:
            risk_threshold: Risk score threshold for flagging
        """
        self.risk_threshold = risk_threshold
        self.pending_reviews: List[Dict] = []
        self.logger = logging.getLogger(__name__)
    
    def should_flag_for_review(self, anomaly_result: Dict) -> bool:
        """
        Determine if request needs human review
        
        Args:
            anomaly_result: Anomaly detection result
            
        Returns:
            True if should flag for review
        """
        return (
            anomaly_result.get("risk_score", 0) >= self.risk_threshold or
            anomaly_result.get("is_anomaly", False)
        )
    
    def flag_for_review(
        self,
        user_id: str,
        input_text: str,
        response: str,
        anomaly_result: Dict
    ):
        """
        Flag request for human review
        
        Args:
            user_id: User identifier
            input_text: Original input
            response: Generated response
            anomaly_result: Anomaly detection result
        """
        review_entry = {
            "user_id": user_id,
            "input": input_text,
            "response": response,
            "anomaly_result": anomaly_result,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        self.pending_reviews.append(review_entry)
        # In production, this would add to a review queue
        self.logger.warning(f"Flagged for human review: {review_entry}")
    
    def get_pending_reviews(self) -> List[Dict]:
        """Get list of pending reviews"""
        return self.pending_reviews.copy()
    
    def clear_review(self, review_id: int):
        """Clear a review (mark as processed)"""
        if 0 <= review_id < len(self.pending_reviews):
            self.pending_reviews[review_id]["status"] = "processed"

