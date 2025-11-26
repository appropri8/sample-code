"""
Model training and export for edge AIoT devices.

Trains simple autoencoder models for anomaly detection and exports
to TensorFlow Lite for edge deployment.
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from typing import Tuple, Dict, Optional
import json
import os


class VibrationAnomalyModel:
    """
    Simple autoencoder for vibration anomaly detection.
    
    Architecture:
    - Encoder: Input → Hidden → Latent (compression)
    - Decoder: Latent → Hidden → Output (reconstruction)
    - Loss: Mean squared error
    - Anomaly score: Reconstruction error
    """
    
    def __init__(self, input_dim: int = 9, latent_dim: int = 3, hidden_dim: int = 6):
        """
        Initialize model architecture.
        
        Args:
            input_dim: Number of input features
            latent_dim: Latent space dimension
            hidden_dim: Hidden layer dimension
        """
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
        self.model = None
        self.threshold = None
    
    def build_model(self) -> keras.Model:
        """Build the autoencoder model."""
        # Input
        input_layer = layers.Input(shape=(self.input_dim,), name='input')
        
        # Encoder
        encoded = layers.Dense(self.hidden_dim, activation='relu', name='encoder_hidden')(input_layer)
        encoded = layers.Dense(self.latent_dim, activation='relu', name='encoder_latent')(encoded)
        
        # Decoder
        decoded = layers.Dense(self.hidden_dim, activation='relu', name='decoder_hidden')(encoded)
        decoded = layers.Dense(self.input_dim, activation='linear', name='decoder_output')(decoded)
        
        # Model
        model = keras.Model(input_layer, decoded, name='vibration_autoencoder')
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        self.model = model
        return model
    
    def train(
        self,
        X_train: np.ndarray,
        X_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Dict:
        """
        Train the model on normal data.
        
        Args:
            X_train: Training features (normal data only)
            X_val: Validation features (normal data only)
            epochs: Number of training epochs
            batch_size: Batch size
            validation_split: Validation split if X_val not provided
        
        Returns:
            Training history
        """
        if self.model is None:
            self.build_model()
        
        # Train
        if X_val is None:
            history = self.model.fit(
                X_train, X_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                verbose=1
            )
        else:
            history = self.model.fit(
                X_train, X_train,
                validation_data=(X_val, X_val),
                epochs=epochs,
                batch_size=batch_size,
                verbose=1
            )
        
        # Compute threshold (95th percentile of reconstruction error on validation set)
        val_predictions = self.model.predict(X_val, verbose=0)
        val_errors = np.mean(np.square(X_val - val_predictions), axis=1)
        self.threshold = np.percentile(val_errors, 95)
        
        return history.history
    
    def predict_anomaly_score(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomaly scores (reconstruction errors).
        
        Args:
            X: Input features
        
        Returns:
            Anomaly scores (higher = more anomalous)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = self.model.predict(X, verbose=0)
        errors = np.mean(np.square(X - predictions), axis=1)
        return errors
    
    def predict_anomaly(self, X: np.ndarray) -> np.ndarray:
        """
        Predict binary anomaly labels.
        
        Args:
            X: Input features
        
        Returns:
            Binary labels (1 = anomaly, 0 = normal)
        """
        scores = self.predict_anomaly_score(X)
        return (scores > self.threshold).astype(int)
    
    def export_to_tflite(
        self,
        output_path: str,
        quantize: bool = True
    ) -> str:
        """
        Export model to TensorFlow Lite format for edge deployment.
        
        Args:
            output_path: Path to save .tflite file
            quantize: Whether to quantize to int8
        
        Returns:
            Path to saved model
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Convert to TensorFlow Lite
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        if quantize:
            # Quantize to int8
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.int8]
            # Representative dataset for quantization (use training data)
            # Note: In production, use actual representative data
            def representative_dataset():
                # This is a placeholder - use actual training data in production
                for _ in range(100):
                    yield [np.random.randn(1, self.input_dim).astype(np.float32)]
            converter.representative_dataset = representative_dataset
        
        tflite_model = converter.convert()
        
        # Save
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        return output_path
    
    def save_metadata(self, output_path: str, model_version: str = "1.0.0"):
        """
        Save model metadata (version, threshold, etc.).
        
        Args:
            output_path: Path to save metadata JSON
            model_version: Model version string
        """
        metadata = {
            'model_version': model_version,
            'input_dim': self.input_dim,
            'latent_dim': self.latent_dim,
            'hidden_dim': self.hidden_dim,
            'threshold': float(self.threshold) if self.threshold is not None else None,
            'model_type': 'autoencoder',
            'task': 'anomaly_detection'
        }
        
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)


def generate_synthetic_vibration_data(
    n_samples: int = 1000,
    n_features: int = 9,
    noise_level: float = 0.1
) -> np.ndarray:
    """
    Generate synthetic vibration data for training/testing.
    
    Args:
        n_samples: Number of samples
        n_features: Number of features (e.g., 3 axes × 3 feature types)
        noise_level: Noise level
    
    Returns:
        Synthetic feature array
    """
    # Generate base patterns (simulating normal vibration)
    t = np.linspace(0, 10, n_samples)
    
    # Create features with some correlation
    features = []
    for i in range(n_features):
        # Different frequencies for different features
        freq = 1.0 + i * 0.5
        base = np.sin(2 * np.pi * freq * t)
        noise = np.random.normal(0, noise_level, n_samples)
        features.append(base + noise)
    
    # Stack and normalize
    X = np.column_stack(features)
    X = (X - np.mean(X, axis=0)) / (np.std(X, axis=0) + 1e-8)
    
    return X

