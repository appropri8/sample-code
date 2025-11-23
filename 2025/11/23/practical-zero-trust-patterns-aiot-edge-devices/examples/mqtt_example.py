"""Example: Mutual TLS MQTT connection"""

import os
import sys
import time
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mqtt_client import (
    create_mqtt_client,
    connect_with_retry,
    on_connect,
    on_message,
    on_disconnect,
    publish_telemetry
)


def main():
    """Example of mTLS MQTT connection"""
    device_id = os.getenv('DEVICE_ID', 'device-001')
    
    print(f"Creating MQTT client for device: {device_id}")
    
    # Create client
    client = create_mqtt_client(device_id)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Connect with retry
    broker_host = os.getenv('MQTT_BROKER_HOST', 'iot.example.com')
    broker_port = int(os.getenv('MQTT_BROKER_PORT', '8883'))
    
    print(f"Connecting to {broker_host}:{broker_port}...")
    
    if connect_with_retry(client, broker_host, broker_port):
        print("✓ Connected successfully")
        
        try:
            # Publish telemetry periodically
            for i in range(5):
                telemetry = {
                    'temperature': 25.5 + i * 0.1,
                    'humidity': 60 + i,
                    'timestamp': int(time.time())
                }
                
                if publish_telemetry(client, device_id, telemetry):
                    print(f"✓ Published telemetry: {json.dumps(telemetry)}")
                else:
                    print("✗ Failed to publish telemetry")
                
                time.sleep(2)
            
            # Keep connection alive
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\nDisconnecting...")
        finally:
            client.loop_stop()
            client.disconnect()
    else:
        print("✗ Failed to connect after retries")
        print("Note: This is a demo. Configure MQTT broker and certificates to run.")


if __name__ == '__main__':
    main()

