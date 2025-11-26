"""
Example: Feature extraction from accelerometer data.

Simulates edge device feature extraction and telemetry publishing.
"""

import numpy as np
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feature_extraction import (
    VibrationFeatureExtractor,
    simulate_accelerometer_data
)
from src.telemetry import TelemetryPublisher, TelemetryCompressor


def main():
    print("Simulating edge device feature extraction...")
    
    # Simulate accelerometer data (1 minute at 1kHz = 60,000 samples)
    print("Generating accelerometer data...")
    accel_data = simulate_accelerometer_data(
        n_samples=60000,
        sample_rate=1000.0,
        frequency=50.0,
        noise_level=0.1
    )
    print(f"Accelerometer data shape: {accel_data.shape}")
    
    # Extract features
    print("\nExtracting features...")
    extractor = VibrationFeatureExtractor(window_size=1024, overlap=0.75)
    features = extractor.extract_features(accel_data)
    print(f"Extracted features shape: {features.shape}")
    print(f"Number of windows: {features.shape[0]}")
    print(f"Features per window: {features.shape[1]}")
    
    # Compute feature statistics (for telemetry)
    print("\nComputing feature statistics...")
    stats = extractor.compute_feature_stats(features)
    
    # Format for telemetry
    telemetry_features = {}
    for feat_name, feat_stats in stats.items():
        telemetry_features[feat_name] = {
            'mean': feat_stats.mean,
            'std': feat_stats.std,
            'min': feat_stats.min,
            'max': feat_stats.max,
            'p25': feat_stats.p25,
            'p50': feat_stats.p50,
            'p75': feat_stats.p75,
            'p95': feat_stats.p95
        }
    
    # Simulate model metrics (in real device, these come from model inference)
    model_metrics = {
        'mean_confidence': 0.94,
        'std_confidence': 0.05,
        'predictions_per_class': {
            'normal': 1000,
            'anomaly': 20
        },
        'low_confidence_count': 5,
        'anomaly_rate': 0.02
    }
    
    # Create telemetry message
    print("\nCreating telemetry message...")
    device_id = "pump-001"
    model_version = "1.2.3"
    
    # Publish telemetry (simulated)
    publisher = TelemetryPublisher(
        broker_host="iot.example.com",
        broker_port=1883,
        compress=True
    )
    
    print(f"Publishing telemetry from device: {device_id}")
    publisher.publish(
        device_id=device_id,
        features=telemetry_features,
        model_metrics=model_metrics,
        model_version=model_version
    )
    
    # Show telemetry payload size
    from src.telemetry import create_telemetry_template
    template = create_telemetry_template()
    template['features'] = telemetry_features
    template['model_metrics'] = model_metrics
    
    compressor = TelemetryCompressor()
    compressed = compressor.compress_message(template)
    
    print(f"\nTelemetry payload size:")
    print(f"  Uncompressed: {len(json.dumps(template))} bytes")
    print(f"  Compressed: {len(compressed)} bytes")
    print(f"  Compression ratio: {len(json.dumps(template)) / len(compressed):.2f}x")
    
    print("\nFeature statistics (sample):")
    for feat_name, feat_stats in list(stats.items())[:3]:
        print(f"  {feat_name}:")
        print(f"    Mean: {feat_stats.mean:.3f}, Std: {feat_stats.std:.3f}")
        print(f"    Range: [{feat_stats.min:.3f}, {feat_stats.max:.3f}]")


if __name__ == '__main__':
    main()

