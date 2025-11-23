"""Tests for privacy filters"""

import pytest
from src.privacy_filters import PrivacyFilter, redact_pii, minimize_telemetry


def test_redact_email():
    """Test email redaction"""
    text = "Contact us at support@example.com"
    result = redact_pii(text)
    assert '[EMAIL_REDACTED]' in result
    assert 'support@example.com' not in result


def test_redact_phone():
    """Test phone number redaction"""
    text = "Call 555-123-4567"
    result = redact_pii(text)
    assert '[PHONE_REDACTED]' in result
    assert '555-123-4567' not in result


def test_redact_ssn():
    """Test SSN redaction"""
    text = "SSN: 123-45-6789"
    result = redact_pii(text)
    assert '[SSN_REDACTED]' in result
    assert '123-45-6789' not in result


def test_minimize_telemetry():
    """Test telemetry minimization"""
    data = {
        'temperature': 25.5,
        'humidity': 60,
        'pressure': 1013.25,
        'location': 'secret'
    }
    allowed = ['temperature', 'humidity']
    result = minimize_telemetry(data, allowed)
    
    assert 'temperature' in result
    assert 'humidity' in result
    assert 'pressure' not in result
    assert 'location' not in result


def test_anonymize_location():
    """Test location anonymization"""
    filter = PrivacyFilter()
    lat, lon = 37.7749123, -122.4194123
    lat_anon, lon_anon = filter.anonymize_location(lat, lon, precision=2)
    
    assert lat_anon == 37.77
    assert lon_anon == -122.42

