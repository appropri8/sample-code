# Drift-Safe AIoT: Monitor, Update, and Roll Back Edge Models

A complete codebase demonstrating how to monitor, detect drift, retrain, and safely roll out model updates for AIoT edge devices.

## Overview

This repository provides practical patterns for keeping AI models on edge devices useful and safe after deployment. It includes:

- **Drift Detection**: Cloud-side statistical tests to detect when models are drifting
- **Model Training**: Train simple autoencoder models for anomaly detection
- **Feature Extraction**: Extract features from sensor data on resource-constrained devices
- **Telemetry**: Compress and publish feature statistics and model metrics
- **Deployment Config**: YAML-based configuration for safe model rollouts

## Features

- **Statistical Drift Detection**: KS test, PSI, mean shift, variance ratio
- **Model Training & Export**: Train autoencoders and export to TensorFlow Lite
- **Low-Bandwidth Telemetry**: Compressed feature statistics for edge devices
- **Safe Rollout Patterns**: Canary and ring-based deployment with automatic rollback
- **Complete Examples**: End-to-end examples from training to deployment

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Train a Model

```bash
python examples/model_training_example.py
```

This will:
- Generate synthetic vibration data
- Train an autoencoder model
- Export to TensorFlow Lite format
- Save model metadata

### 2. Extract Features (Simulated Edge Device)

```bash
python examples/feature_extraction_example.py
```

This will:
- Simulate accelerometer data
- Extract features (RMS, peak, kurtosis)
- Compute feature statistics
- Create telemetry message

### 3. Detect Drift

```bash
python examples/drift_detection_example.py \
  --recent recent_features.csv \
  --baseline baseline_features.csv \
  --window-size 7
```

This will:
- Compare recent data to baseline
- Run statistical tests (KS test, mean shift, variance)
- Print drift report
- Return exit code: 0 = no action, 1 = retrain needed

## Architecture

### Components

1. **Feature Extraction** (`src/feature_extraction.py`): Extract features from sensor data on edge devices
2. **Drift Detection** (`src/drift_detection.py`): Cloud-side drift detection using statistical tests
3. **Model Training** (`src/model_training.py`): Train and export models for edge deployment
4. **Telemetry** (`src/telemetry.py`): Compress and publish telemetry from edge devices

### Workflow

```
Edge Device → Feature Extraction → Telemetry → Cloud
                                              ↓
                                    Drift Detection
                                              ↓
                                    Retrain Model
                                              ↓
                                    Rollout (Canary → Ring 1 → Ring 2)
                                              ↓
                                    Monitor & Rollback if needed
```

## Usage Examples

### Drift Detection

```python
from src.drift_detection import DriftDetector
import pandas as pd

# Load data
recent_data = pd.read_csv('recent_features.csv')
baseline_data = pd.read_csv('baseline_features.csv')

# Detect drift
detector = DriftDetector(baseline_window_days=30, recent_window_days=7)
result = detector.detect_drift(recent_data, baseline_data, 'vibration_rms')

if result.drift_detected:
    print(f"Drift detected: {result.drift_type} (severity: {result.severity})")
    # Trigger retraining
else:
    print("No drift detected")
```

### Model Training

```python
from src.model_training import VibrationAnomalyModel
import numpy as np

# Generate training data
X_train = generate_synthetic_vibration_data(n_samples=5000, n_features=9)
X_val = generate_synthetic_vibration_data(n_samples=1000, n_features=9)

# Train model
model = VibrationAnomalyModel(input_dim=9, latent_dim=3, hidden_dim=6)
model.build_model()
model.train(X_train, X_val, epochs=100, batch_size=32)

# Export to TensorFlow Lite
model.export_to_tflite('model.tflite', quantize=True)
model.save_metadata('metadata.json', model_version='1.0.0')
```

### Feature Extraction

```python
from src.feature_extraction import VibrationFeatureExtractor
import numpy as np

# Simulate accelerometer data
accel_data = simulate_accelerometer_data(n_samples=60000, sample_rate=1000.0)

# Extract features
extractor = VibrationFeatureExtractor(window_size=1024, overlap=0.75)
features = extractor.extract_features(accel_data)

# Compute statistics for telemetry
stats = extractor.compute_feature_stats(features)
```

### Telemetry Publishing

```python
from src.telemetry import TelemetryPublisher

# Initialize publisher
publisher = TelemetryPublisher(
    broker_host='iot.example.com',
    broker_port=1883,
    compress=True
)

# Publish telemetry
publisher.publish(
    device_id='pump-001',
    features=feature_stats,
    model_metrics=model_metrics,
    model_version='1.2.3'
)
```

## Deployment Configuration

See `config/deployment.yaml` for rollout configuration:

- **Rollout Rings**: Ring 0 (lab) → Ring 1 (canary) → Ring 2 (full fleet)
- **Rollback Conditions**: Automatic rollback on false alarm increase, confidence drop, etc.
- **Safe Mode**: Fallback to rules-based logic if model health degrades

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=src --cov-report=html
```

## Code Structure

```
.
├── src/
│   ├── drift_detection.py      # Cloud-side drift detection
│   ├── model_training.py        # Model training and export
│   ├── feature_extraction.py    # Edge device feature extraction
│   └── telemetry.py             # Telemetry compression and publishing
├── examples/
│   ├── drift_detection_example.py
│   ├── model_training_example.py
│   └── feature_extraction_example.py
├── tests/
│   ├── test_drift_detection.py
│   ├── test_model_training.py
│   └── test_feature_extraction.py
├── config/
│   └── deployment.yaml          # Deployment configuration
└── README.md
```

## Design Principles

1. **Simple Statistics**: Use mean, variance, min, max for telemetry (not raw data)
2. **Statistical Tests**: KS test, PSI, mean shift for drift detection (not complex ML)
3. **Low Bandwidth**: Compress telemetry, batch messages, use quantized models
4. **Safe Rollouts**: Canary → Ring 1 → Ring 2 with automatic rollback
5. **Fail Secure**: Roll back if metrics degrade, fall back to rules if model breaks

## Limitations

- Model training uses synthetic data (replace with real data in production)
- Telemetry publishing is simulated (use real MQTT client in production)
- Feature extraction is Python (use C++/MicroPython for actual edge devices)
- Drift detection is simplified (add more sophisticated tests for production)

## Production Considerations

- **Key Management**: Store model signing keys securely
- **Certificate Rotation**: Implement certificate rotation for OTA updates
- **Policy Updates**: Update deployment policies via signed channels
- **Audit Logging**: Log all drift events, rollouts, and rollbacks
- **Monitoring**: Set up dashboards for fleet-wide model health
- **SLOs**: Define service level objectives (false alarm rate, confidence scores)

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Consider edge device constraints (memory, CPU, bandwidth)
4. Test with various drift scenarios

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

## Related Articles

- [Drift-Safe AIoT: How to Monitor, Update, and Roll Back Edge Models in the Field](https://appropri8.com/blog/2025/11/26/drift-safe-aiot-monitor-update-rollback-edge-models/)

