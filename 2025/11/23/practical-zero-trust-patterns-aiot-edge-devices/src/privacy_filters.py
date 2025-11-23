"""Privacy filters for edge devices: PII redaction and data minimization"""

import re
from typing import Dict, Any, List


class PrivacyFilter:
    """Basic PII redaction and data minimization"""
    
    # Simple regex patterns (use proper tools in production)
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b')
    
    def redact_pii(self, text: str) -> str:
        """Redact PII from text"""
        # Redact emails
        text = self.EMAIL_PATTERN.sub('[EMAIL_REDACTED]', text)
        
        # Redact phone numbers
        text = self.PHONE_PATTERN.sub('[PHONE_REDACTED]', text)
        
        # Redact SSNs
        text = self.SSN_PATTERN.sub('[SSN_REDACTED]', text)
        
        # Redact credit cards
        text = self.CREDIT_CARD_PATTERN.sub('[CARD_REDACTED]', text)
        
        return text
    
    def minimize_telemetry(self, data: Dict[str, Any], allowed_fields: List[str]) -> Dict[str, Any]:
        """Minimize telemetry to only allowed fields"""
        return {k: v for k, v in data.items() if k in allowed_fields}
    
    def anonymize_location(self, lat: float, lon: float, precision: int = 2) -> tuple:
        """Anonymize location by rounding to specified precision"""
        # Round to N decimal places (roughly 100m for 2 decimal places)
        lat_rounded = round(lat, precision)
        lon_rounded = round(lon, precision)
        return lat_rounded, lon_rounded


def redact_pii(text: str) -> str:
    """Redact PII from text (convenience function)"""
    filter = PrivacyFilter()
    return filter.redact_pii(text)


def minimize_telemetry(data: Dict[str, Any], allowed_fields: List[str]) -> Dict[str, Any]:
    """Minimize telemetry to only allowed fields (convenience function)"""
    filter = PrivacyFilter()
    return filter.minimize_telemetry(data, allowed_fields)

