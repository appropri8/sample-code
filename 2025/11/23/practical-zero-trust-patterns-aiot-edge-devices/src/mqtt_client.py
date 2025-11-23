"""Mutual TLS MQTT client for edge devices"""

import paho.mqtt.client as mqtt
import ssl
import os
import time
import json


def create_mqtt_client(client_id, device_cert_path=None, device_key_path=None, ca_cert_path=None):
    """Create MQTT client with mTLS"""
    # Default paths
    if device_cert_path is None:
        device_cert_path = os.getenv('DEVICE_CERT', '/etc/device/certs/device.crt')
    if device_key_path is None:
        device_key_path = os.getenv('DEVICE_KEY', '/etc/device/certs/device.key')
    if ca_cert_path is None:
        ca_cert_path = os.getenv('CA_CERT', '/etc/device/certs/ca.crt')
    
    client = mqtt.Client(client_id=client_id)
    
    # Configure TLS
    context = ssl.create_default_context(
        cafile=ca_cert_path,
        capath=None,
        cadata=None
    )
    
    # Load client certificate and key
    context.load_cert_chain(device_cert_path, device_key_path)
    
    # Require TLS 1.2 or higher
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    # Set TLS context
    client.tls_set_context(context)
    
    return client


def on_connect(client, userdata, flags, rc):
    """Callback for when client connects"""
    if rc == 0:
        print("Connected to MQTT broker")
        # Subscribe to device-specific topic
        device_id = client._client_id.decode() if isinstance(client._client_id, bytes) else client._client_id
        client.subscribe(f"devices/{device_id}/commands")
    else:
        print(f"Connection failed: {rc}")


def on_message(client, userdata, msg):
    """Callback for when message is received"""
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"Received message on {topic}: {payload}")


def on_disconnect(client, userdata, rc):
    """Callback for when client disconnects"""
    print(f"Disconnected: {rc}")


def connect_with_retry(client, broker_host=None, broker_port=None, max_retries=5):
    """Connect to broker with retry logic"""
    if broker_host is None:
        broker_host = os.getenv('MQTT_BROKER_HOST', 'iot.example.com')
    if broker_port is None:
        broker_port = int(os.getenv('MQTT_BROKER_PORT', '8883'))
    
    for attempt in range(max_retries):
        try:
            client.connect(broker_host, broker_port, keepalive=60)
            client.loop_start()
            return True
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return False
    return False


def publish_telemetry(client, device_id, telemetry_data):
    """Publish telemetry data"""
    topic = f"devices/{device_id}/telemetry"
    payload = json.dumps(telemetry_data)
    result = client.publish(topic, payload)
    return result.rc == mqtt.MQTT_ERR_SUCCESS

