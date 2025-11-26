"""Tests for model training module."""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import os

from src.model_training import VibrationAnomalyModel, generate_synthetic_vibration_data


def test_model_build():
    """Test model architecture building."""
    model = VibrationAnomalyModel(input_dim=9, latent_dim=3, hidden_dim=6)
    built_model = model.build_model()
    
    assert built_model is not None
    assert built_model.input_shape == (None, 9)
    assert built_model.output_shape == (None, 9)


def test_model_training():
    """Test model training."""
    model = VibrationAnomalyModel(input_dim=9, latent_dim=3, hidden_dim=6)
    model.build_model()
    
    # Generate training data
    X_train = generate_synthetic_vibration_data(n_samples=500, n_features=9)
    X_val = generate_synthetic_vibration_data(n_samples=100, n_features=9)
    
    # Train
    history = model.train(
        X_train=X_train,
        X_val=X_val,
        epochs=10,
        batch_size=32
    )
    
    # Check training completed
    assert 'loss' in history
    assert 'val_loss' in history
    assert len(history['loss']) == 10
    
    # Check threshold set
    assert model.threshold is not None
    assert model.threshold > 0


def test_anomaly_prediction():
    """Test anomaly prediction."""
    model = VibrationAnomalyModel(input_dim=9, latent_dim=3, hidden_dim=6)
    model.build_model()
    
    # Generate and train
    X_train = generate_synthetic_vibration_data(n_samples=500, n_features=9)
    X_val = generate_synthetic_vibration_data(n_samples=100, n_features=9)
    model.train(X_train, X_val, epochs=10, batch_size=32)
    
    # Predict
    X_test = generate_synthetic_vibration_data(n_samples=50, n_features=9)
    scores = model.predict_anomaly_score(X_test)
    predictions = model.predict_anomaly(X_test)
    
    assert len(scores) == 50
    assert len(predictions) == 50
    assert all(score >= 0 for score in scores)
    assert all(pred in [0, 1] for pred in predictions)


def test_model_export():
    """Test model export to TensorFlow Lite."""
    model = VibrationAnomalyModel(input_dim=9, latent_dim=3, hidden_dim=6)
    model.build_model()
    
    # Generate and train
    X_train = generate_synthetic_vibration_data(n_samples=500, n_features=9)
    X_val = generate_synthetic_vibration_data(n_samples=100, n_features=9)
    model.train(X_train, X_val, epochs=10, batch_size=32)
    
    # Export
    with tempfile.TemporaryDirectory() as tmpdir:
        tflite_path = os.path.join(tmpdir, "test_model.tflite")
        model.export_to_tflite(tflite_path, quantize=False)
        
        # Check file exists
        assert os.path.exists(tflite_path)
        assert os.path.getsize(tflite_path) > 0


def test_metadata_save():
    """Test metadata saving."""
    model = VibrationAnomalyModel(input_dim=9, latent_dim=3, hidden_dim=6)
    model.build_model()
    
    # Generate and train
    X_train = generate_synthetic_vibration_data(n_samples=500, n_features=9)
    X_val = generate_synthetic_vibration_data(n_samples=100, n_features=9)
    model.train(X_train, X_val, epochs=10, batch_size=32)
    
    # Save metadata
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = os.path.join(tmpdir, "metadata.json")
        model.save_metadata(metadata_path, model_version="1.0.0")
        
        # Check file exists and is valid JSON
        assert os.path.exists(metadata_path)
        import json
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata['model_version'] == "1.0.0"
        assert metadata['input_dim'] == 9
        assert metadata['threshold'] is not None

