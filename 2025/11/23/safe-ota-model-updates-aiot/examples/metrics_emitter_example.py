"""Example: Metrics collection and reporting."""

import os
import time
from src.metrics_emitter import MetricsEmitter

def main():
    """Run metrics emitter example."""
    device_id = os.getenv("DEVICE_ID", "device-001")
    
    # Create metrics emitter (without MQTT, uses HTTP)
    emitter = MetricsEmitter(device_id, mqtt_client=None)
    
    print(f"Metrics emitter started for device: {device_id}")
    
    # Simulate some inferences
    print("\nSimulating inferences...")
    for i in range(20):
        latency = 40.0 + (i % 5) * 5  # Varying latency
        success = i % 20 != 0  # One failure every 20 inferences
        emitter.record_inference(latency, success)
        time.sleep(0.1)
    
    # Emit metrics
    print("\nEmitting metrics...")
    success = emitter.emit_metrics()
    
    if success:
        print("✓ Metrics emitted successfully")
    else:
        print("✗ Metrics emission failed")
        print("  (This is expected if metrics service is not available)")

if __name__ == "__main__":
    main()

