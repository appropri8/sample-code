"""Input sanitisation for safe prompt pipelines"""

import re
import logging
from typing import Tuple, List

class InputSanitiser:
    """Sanitise user inputs before use in prompts"""
    
    # Patterns that might indicate injection attempts
    SUSPICIOUS_PATTERNS = [
        r"ignore\s+(previous|all|the)\s+instructions?",
        r"forget\s+(previous|all|everything)",
        r"system\s+prompt",
        r"repeat\s+(your|the)\s+instructions?",
        r"what\s+(are|were)\s+your\s+instructions?",
        r"tell\s+me\s+your\s+prompt",
        r"reveal\s+your\s+instructions",
        r"what\s+were\s+you\s+told",
    ]
    
    def __init__(self, max_length: int = 2000):
        """
        Initialize sanitizer
        
        Args:
            max_length: Maximum allowed input length
        """
        self.max_length = max_length
        self.logger = logging.getLogger(__name__)
    
    def sanitise(self, user_input: str) -> Tuple[str, List[str]]:
        """
        Sanitise input and return cleaned version + detected patterns
        
        Args:
            user_input: Raw user input to sanitise
            
        Returns:
            Tuple of (sanitised_input, suspicious_patterns)
        """
        if not user_input:
            return "", []
        
        # Normalise whitespace
        cleaned = re.sub(r'\s+', ' ', user_input.strip())
        
        # Check length
        original_length = len(cleaned)
        if len(cleaned) > self.max_length:
            cleaned = cleaned[:self.max_length]
            self.logger.warning(
                f"Input truncated from {original_length} to {self.max_length} characters"
            )
        
        # Detect suspicious patterns
        suspicious = []
        for pattern in self.SUSPICIOUS_PATTERNS:
            matches = re.findall(pattern, cleaned, re.IGNORECASE)
            if matches:
                suspicious.append(pattern)
                self.logger.warning(f"Suspicious pattern detected: {pattern}")
        
        # Escape special delimiters that might break role separation
        # Replace newlines with spaces to prevent prompt injection via formatting
        cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
        
        # Remove excessive punctuation that might confuse models
        cleaned = re.sub(r'[!]{3,}', '!', cleaned)  # Multiple exclamation marks
        cleaned = re.sub(r'[?]{3,}', '?', cleaned)  # Multiple question marks
        
        return cleaned, suspicious

