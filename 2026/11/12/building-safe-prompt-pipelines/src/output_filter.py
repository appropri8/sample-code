"""Output filtering for safe prompt pipelines"""

import re
import logging
from typing import List

class OutputFilter:
    """Filter outputs for safety"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Patterns that might indicate sensitive content
        self.blocked_patterns = [
            r"system\s+prompt\s*:",
            r"instructions\s*:",
            r"your\s+instructions\s+are",
        ]
    
    def filter(self, content: str) -> str:
        """
        Filter potentially sensitive content
        
        Args:
            content: Output content to filter
            
        Returns:
            Filtered content
        """
        if not content:
            return content
        
        for pattern in self.blocked_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Replace with generic message
                self.logger.warning(f"Blocked pattern detected in output: {pattern}")
                return "I can't provide that information."
        
        return content

