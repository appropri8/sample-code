"""
Telemetry patterns for edge AIoT devices.

Handles compression, batching, and MQTT publishing of feature
statistics and model metrics from edge devices.
"""

import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import gzip
import base64


@dataclass
class TelemetryMessage:
    """Telemetry message structure."""
    device_id: str
    timestamp: str
    model_version: str
    features: Dict[str, Dict[str, float]]
    model_metrics: Dict[str, any]
    message_id: Optional[str] = None


class TelemetryCompressor:
    """
    Compresses telemetry messages for low-bandwidth transmission.
    """
    
    @staticmethod
    def compress_message(message: Dict) -> str:
        """
        Compress a telemetry message using gzip and base64.
        
        Args:
            message: Telemetry message dict
        
        Returns:
            Compressed base64 string
        """
        json_str = json.dumps(message)
        compressed = gzip.compress(json_str.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('utf-8')
        return encoded
    
    @staticmethod
    def decompress_message(compressed: str) -> Dict:
        """
        Decompress a telemetry message.
        
        Args:
            compressed: Compressed base64 string
        
        Returns:
            Decompressed message dict
        """
        decoded = base64.b64decode(compressed.encode('utf-8'))
        decompressed = gzip.decompress(decoded)
        message = json.loads(decompressed.decode('utf-8'))
        return message


class TelemetryPublisher:
    """
    Publishes telemetry to MQTT broker (simulated for this example).
    
    In production, use paho-mqtt or similar library.
    """
    
    def __init__(self, broker_host: str, broker_port: int = 1883, compress: bool = True):
        """
        Initialize telemetry publisher.
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            compress: Whether to compress messages
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.compress = compress
        self.compressor = TelemetryCompressor()
        # In production, initialize MQTT client here
        # self.client = mqtt.Client()
    
    def publish(
        self,
        device_id: str,
        features: Dict[str, Dict[str, float]],
        model_metrics: Dict[str, any],
        model_version: str = "1.0.0"
    ) -> bool:
        """
        Publish telemetry message.
        
        Args:
            device_id: Device identifier
            features: Feature statistics
            model_metrics: Model performance metrics
            model_version: Model version string
        
        Returns:
            True if published successfully
        """
        message = TelemetryMessage(
            device_id=device_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            model_version=model_version,
            features=features,
            model_metrics=model_metrics
        )
        
        message_dict = asdict(message)
        
        # Compress if enabled
        if self.compress:
            payload = self.compressor.compress_message(message_dict)
        else:
            payload = json.dumps(message_dict)
        
        # Publish to MQTT (simulated)
        topic = f"fleet/{device_id}/ml-metrics"
        # In production: self.client.publish(topic, payload)
        print(f"[MQTT] Publishing to {topic}: {len(payload)} bytes")
        
        return True
    
    def publish_batch(
        self,
        device_id: str,
        feature_batch: List[Dict[str, Dict[str, float]]],
        model_metrics_batch: List[Dict[str, any]],
        model_version: str = "1.0.0"
    ) -> bool:
        """
        Publish batched telemetry messages.
        
        Args:
            device_id: Device identifier
            feature_batch: List of feature statistics
            model_metrics_batch: List of model metrics
            model_version: Model version string
        
        Returns:
            True if published successfully
        """
        # Combine batch into single message
        combined_features = {}
        combined_metrics = {
            'mean_confidence': [],
            'anomaly_rate': []
        }
        
        for features, metrics in zip(feature_batch, model_metrics_batch):
            # Merge feature stats (average them)
            for feat_name, feat_stats in features.items():
                if feat_name not in combined_features:
                    combined_features[feat_name] = {
                        'mean': [],
                        'std': [],
                        'min': [],
                        'max': []
                    }
                combined_features[feat_name]['mean'].append(feat_stats.get('mean', 0))
                combined_features[feat_name]['std'].append(feat_stats.get('std', 0))
                combined_features[feat_name]['min'].append(feat_stats.get('min', 0))
                combined_features[feat_name]['max'].append(feat_stats.get('max', 0))
            
            # Merge model metrics
            if 'mean_confidence' in metrics:
                combined_metrics['mean_confidence'].append(metrics['mean_confidence'])
            if 'anomaly_rate' in metrics:
                combined_metrics['anomaly_rate'].append(metrics['anomaly_rate'])
        
        # Average combined features
        for feat_name in combined_features:
            combined_features[feat_name] = {
                'mean': sum(combined_features[feat_name]['mean']) / len(combined_features[feat_name]['mean']),
                'std': sum(combined_features[feat_name]['std']) / len(combined_features[feat_name]['std']),
                'min': min(combined_features[feat_name]['min']),
                'max': max(combined_features[feat_name]['max'])
            }
        
        # Average combined metrics
        if combined_metrics['mean_confidence']:
            combined_metrics['mean_confidence'] = sum(combined_metrics['mean_confidence']) / len(combined_metrics['mean_confidence'])
        if combined_metrics['anomaly_rate']:
            combined_metrics['anomaly_rate'] = sum(combined_metrics['anomaly_rate']) / len(combined_metrics['anomaly_rate'])
        
        return self.publish(device_id, combined_features, combined_metrics, model_version)


def create_telemetry_template() -> Dict:
    """
    Create a telemetry message template.
    
    Returns:
        Template dict
    """
    return {
        "device_id": "device-001",
        "timestamp": "2025-11-26T10:00:00Z",
        "model_version": "1.2.3",
        "features": {
            "x_rms": {
                "mean": 2.5,
                "std": 0.3,
                "min": 2.0,
                "max": 3.1,
                "p25": 2.2,
                "p50": 2.5,
                "p75": 2.8,
                "p95": 3.0
            }
        },
        "model_metrics": {
            "mean_confidence": 0.94,
            "std_confidence": 0.05,
            "predictions_per_class": {
                "normal": 1000,
                "anomaly": 20
            },
            "low_confidence_count": 5
        }
    }

