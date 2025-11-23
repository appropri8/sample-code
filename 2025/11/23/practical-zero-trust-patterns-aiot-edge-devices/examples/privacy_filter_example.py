"""Example: Privacy filters for PII redaction and data minimization"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.privacy_filters import redact_pii, minimize_telemetry, PrivacyFilter


def main():
    """Example of privacy filtering"""
    print("Privacy Filter Examples\n")
    
    # Example 1: PII Redaction
    print("1. PII Redaction:")
    text_with_pii = """
    Contact John Doe at john.doe@example.com or call 555-123-4567.
    SSN: 123-45-6789
    Credit card: 4532-1234-5678-9010
    """
    
    print("Original text:")
    print(text_with_pii)
    
    redacted = redact_pii(text_with_pii)
    print("\nRedacted text:")
    print(redacted)
    
    # Example 2: Telemetry Minimization
    print("\n2. Telemetry Minimization:")
    full_telemetry = {
        'temperature': 25.5,
        'humidity': 60,
        'pressure': 1013.25,
        'location_lat': 37.7749,
        'location_lon': -122.4194,
        'device_id': 'device-001',
        'timestamp': 1234567890,
        'battery_level': 85,
        'signal_strength': -70
    }
    
    print("Full telemetry:")
    print(full_telemetry)
    
    # Only send essential fields
    allowed_fields = ['temperature', 'humidity', 'timestamp']
    minimized = minimize_telemetry(full_telemetry, allowed_fields)
    
    print(f"\nMinimized telemetry (allowed fields: {allowed_fields}):")
    print(minimized)
    
    # Example 3: Location Anonymization
    print("\n3. Location Anonymization:")
    filter = PrivacyFilter()
    
    exact_location = (37.7749123, -122.4194123)
    print(f"Exact location: {exact_location}")
    
    anonymized = filter.anonymize_location(*exact_location, precision=2)
    print(f"Anonymized location (2 decimal places): {anonymized}")
    
    # Example 4: Combined Privacy Pipeline
    print("\n4. Combined Privacy Pipeline:")
    raw_data = {
        'sensor_readings': {
            'temperature': 25.5,
            'humidity': 60
        },
        'user_message': 'Contact support at support@example.com',
        'location': {
            'lat': 37.7749123,
            'lon': -122.4194123
        },
        'device_id': 'device-001',
        'timestamp': 1234567890
    }
    
    print("Raw data:")
    print(raw_data)
    
    # Apply privacy filters
    processed_data = raw_data.copy()
    
    # Redact PII from user message
    if 'user_message' in processed_data:
        processed_data['user_message'] = redact_pii(processed_data['user_message'])
    
    # Anonymize location
    if 'location' in processed_data:
        lat, lon = processed_data['location']['lat'], processed_data['location']['lon']
        lat_anon, lon_anon = filter.anonymize_location(lat, lon, precision=2)
        processed_data['location'] = {'lat': lat_anon, 'lon': lon_anon}
    
    # Minimize to essential fields only
    essential_fields = ['sensor_readings', 'timestamp']
    processed_data = minimize_telemetry(processed_data, essential_fields)
    
    print("\nProcessed data (privacy filters applied):")
    print(processed_data)


if __name__ == '__main__':
    main()

