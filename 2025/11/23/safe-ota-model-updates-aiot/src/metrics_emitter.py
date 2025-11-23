"""Metrics emitter for sending device metrics to cloud."""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
import requests


class MetricsEmitter:
    """Emits device metrics to cloud."""
    
    def __init__(self, device_id: str, mqtt_client: Optional[mqtt.Client] = None):
        """Initialize metrics emitter.
        
        Args:
            device_id: Device identifier
            mqtt_client: Optional MQTT client (if None, uses HTTP)
        """
        self.device_id = device_id
        self.mqtt_client = mqtt_client
        self.metrics_service_url = os.getenv("METRICS_SERVICE_URL", "https://metrics.example.com")
        self.inference_count = 0
        self.error_count = 0
        self.latency_sum = 0.0
        self.start_time = time.time()
    
    def record_inference(self, latency_ms: float, success: bool = True):
        """Record a single inference.
        
        Args:
            latency_ms: Inference latency in milliseconds
            success: Whether inference succeeded
        """
        self.inference_count += 1
        if success:
            self.latency_sum += latency_ms
        else:
            self.error_count += 1
    
    def emit_metrics(self) -> bool:
        """Emit metrics to cloud via MQTT or HTTP.
        
        Returns:
            True if metrics emitted successfully, False otherwise
        """
        elapsed = time.time() - self.start_time
        
        avg_latency = 0.0
        if self.inference_count > self.error_count:
            avg_latency_count = self.inference_count - self.error_count
            avg_latency = self.latency_sum / avg_latency_count
        
        error_rate = 0.0
        if self.inference_count > 0:
            error_rate = self.error_count / self.inference_count
        
        metrics = {
            "device_id": self.device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": self.get_current_model_version(),
            "avg_latency_ms": avg_latency,
            "num_inferences": self.inference_count,
            "num_errors": self.error_count,
            "error_rate": error_rate,
            "cpu_percent": self.get_cpu_usage(),
            "ram_percent": self.get_ram_usage(),
            "uptime_seconds": elapsed
        }
        
        if self.mqtt_client:
            return self._emit_mqtt(metrics)
        else:
            return self._emit_http(metrics)
    
    def _emit_mqtt(self, metrics: Dict[str, Any]) -> bool:
        """Emit metrics via MQTT.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            topic = f"devices/{self.device_id}/metrics"
            payload = json.dumps(metrics)
            
            result = self.mqtt_client.publish(topic, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                # Reset counters
                self._reset_counters()
                return True
            else:
                print(f"MQTT publish failed: {result.rc}")
                return False
        except Exception as e:
            print(f"MQTT emit error: {e}")
            return False
    
    def _emit_http(self, metrics: Dict[str, Any]) -> bool:
        """Emit metrics via HTTP POST.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.metrics_service_url}/devices/{self.device_id}/metrics"
            response = requests.post(
                url,
                json=metrics,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                # Reset counters
                self._reset_counters()
                return True
            else:
                print(f"HTTP metrics emit failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"HTTP emit error: {e}")
            return False
    
    def _reset_counters(self):
        """Reset metrics counters."""
        self.inference_count = 0
        self.error_count = 0
        self.latency_sum = 0.0
        self.start_time = time.time()
    
    def get_current_model_version(self) -> str:
        """Get current model version.
        
        Returns:
            Model version string
        """
        # Read from model metadata
        import json
        from pathlib import Path
        
        current_slot_path = Path("/tmp/models/current_slot")
        if current_slot_path.exists():
            with open(current_slot_path, "r") as f:
                slot = f.read().strip()
                metadata_path = Path(f"/tmp/models/slot_{slot.lower()}/metadata.json")
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        return metadata.get("version", "unknown")
        return "unknown"
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage.
        
        Returns:
            CPU usage percentage
        """
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except Exception:
            return 0.0
    
    def get_ram_usage(self) -> float:
        """Get current RAM usage percentage.
        
        Returns:
            RAM usage percentage
        """
        try:
            import psutil
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0

