"""
Example: Train and export model for edge deployment.

Trains a simple autoencoder for anomaly detection and exports to TensorFlow Lite.
"""

import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.model_training import VibrationAnomalyModel, generate_synthetic_vibration_data


def main():
    print("Training vibration anomaly detection model...")
    
    # Generate synthetic training data (normal vibration patterns)
    print("Generating training data...")
    X_train = generate_synthetic_vibration_data(n_samples=5000, n_features=9, noise_level=0.1)
    X_val = generate_synthetic_vibration_data(n_samples=1000, n_features=9, noise_level=0.1)
    
    print(f"Training data shape: {X_train.shape}")
    print(f"Validation data shape: {X_val.shape}")
    
    # Initialize model
    model = VibrationAnomalyModel(input_dim=9, latent_dim=3, hidden_dim=6)
    model.build_model()
    
    print("\nModel architecture:")
    model.model.summary()
    
    # Train model
    print("\nTraining model...")
    history = model.train(
        X_train=X_train,
        X_val=X_val,
        epochs=50,
        batch_size=32
    )
    
    print(f"\nTraining complete!")
    print(f"Final training loss: {history['loss'][-1]:.4f}")
    print(f"Final validation loss: {history['val_loss'][-1]:.4f}")
    print(f"Anomaly threshold (95th percentile): {model.threshold:.4f}")
    
    # Test on validation data
    print("\nEvaluating on validation data...")
    val_scores = model.predict_anomaly_score(X_val)
    val_predictions = model.predict_anomaly(X_val)
    
    print(f"Mean anomaly score: {np.mean(val_scores):.4f}")
    print(f"Anomaly rate: {np.mean(val_predictions):.2%}")
    
    # Export to TensorFlow Lite
    output_dir = Path(__file__).parent.parent / "models"
    output_dir.mkdir(exist_ok=True)
    
    tflite_path = output_dir / "vibration_anomaly.tflite"
    print(f"\nExporting to TensorFlow Lite: {tflite_path}")
    model.export_to_tflite(str(tflite_path), quantize=True)
    
    # Save metadata
    metadata_path = output_dir / "vibration_anomaly_metadata.json"
    model.save_metadata(str(metadata_path), model_version="1.0.0")
    
    print(f"Model exported successfully!")
    print(f"  TFLite model: {tflite_path}")
    print(f"  Metadata: {metadata_path}")
    print(f"  Model size: {tflite_path.stat().st_size / 1024:.2f} KB")


if __name__ == '__main__':
    main()

