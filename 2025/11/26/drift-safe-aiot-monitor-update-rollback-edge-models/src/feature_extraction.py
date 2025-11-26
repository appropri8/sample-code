"""
Feature extraction patterns for edge AIoT devices.

Computes features from raw sensor data (e.g., accelerometer) for
anomaly detection models. Designed for resource-constrained devices.
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class FeatureStats:
    """Statistics for a feature window."""
    mean: float
    std: float
    min: float
    max: float
    p25: float
    p50: float
    p75: float
    p95: float


class VibrationFeatureExtractor:
    """
    Extracts features from accelerometer data for vibration anomaly detection.
    
    Features:
    - RMS (root mean square) per axis
    - Peak value per axis
    - Kurtosis per axis
    - Frequency domain features (optional)
    """
    
    def __init__(self, window_size: int = 1024, overlap: float = 0.75):
        """
        Initialize feature extractor.
        
        Args:
            window_size: Number of samples per window
            overlap: Overlap ratio between windows (0.0 to 1.0)
        """
        self.window_size = window_size
        self.overlap = overlap
        self.step_size = int(window_size * (1 - overlap))
    
    def extract_features(self, accel_data: np.ndarray) -> np.ndarray:
        """
        Extract features from accelerometer data.
        
        Args:
            accel_data: Array of shape (n_samples, 3) for 3-axis accelerometer
        
        Returns:
            Feature array of shape (n_windows, n_features)
        """
        if accel_data.shape[1] != 3:
            raise ValueError("Expected 3-axis accelerometer data (n_samples, 3)")
        
        features = []
        
        # Slide window over data
        for i in range(0, len(accel_data) - self.window_size + 1, self.step_size):
            window = accel_data[i:i + self.window_size]
            
            # Extract features for this window
            window_features = self._extract_window_features(window)
            features.append(window_features)
        
        return np.array(features)
    
    def _extract_window_features(self, window: np.ndarray) -> np.ndarray:
        """
        Extract features from a single window.
        
        Args:
            window: Array of shape (window_size, 3)
        
        Returns:
            Feature vector
        """
        features = []
        
        # For each axis (x, y, z)
        for axis in range(3):
            axis_data = window[:, axis]
            
            # RMS (root mean square)
            rms = np.sqrt(np.mean(axis_data ** 2))
            features.append(rms)
            
            # Peak value
            peak = np.max(np.abs(axis_data))
            features.append(peak)
            
            # Kurtosis (tailedness)
            if len(axis_data) > 3:
                kurtosis = self._compute_kurtosis(axis_data)
            else:
                kurtosis = 0.0
            features.append(kurtosis)
        
        return np.array(features)
    
    def _compute_kurtosis(self, data: np.ndarray) -> float:
        """
        Compute kurtosis (fourth moment).
        
        Args:
            data: Input data
        
        Returns:
            Kurtosis value
        """
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return 0.0
        
        normalized = (data - mean) / std
        kurtosis = np.mean(normalized ** 4) - 3.0  # Excess kurtosis
        
        return float(kurtosis)
    
    def compute_feature_stats(self, features: np.ndarray) -> Dict[str, FeatureStats]:
        """
        Compute statistics for extracted features (for telemetry).
        
        Args:
            features: Feature array of shape (n_windows, n_features)
        
        Returns:
            Dict mapping feature names to statistics
        """
        feature_names = []
        for axis in ['x', 'y', 'z']:
            for feat_type in ['rms', 'peak', 'kurtosis']:
                feature_names.append(f'{axis}_{feat_type}')
        
        stats = {}
        for i, name in enumerate(feature_names):
            values = features[:, i]
            stats[name] = FeatureStats(
                mean=float(np.mean(values)),
                std=float(np.std(values)),
                min=float(np.min(values)),
                max=float(np.max(values)),
                p25=float(np.percentile(values, 25)),
                p50=float(np.percentile(values, 50)),
                p75=float(np.percentile(values, 75)),
                p95=float(np.percentile(values, 95))
            )
        
        return stats


def simulate_accelerometer_data(
    n_samples: int = 10000,
    sample_rate: float = 1000.0,
    frequency: float = 50.0,
    noise_level: float = 0.1
) -> np.ndarray:
    """
    Simulate accelerometer data for testing.
    
    Args:
        n_samples: Number of samples
        sample_rate: Sampling rate (Hz)
        frequency: Dominant frequency (Hz)
        noise_level: Noise level
    
    Returns:
        Accelerometer data of shape (n_samples, 3)
    """
    t = np.arange(n_samples) / sample_rate
    
    # Generate 3-axis data with different phases
    x = np.sin(2 * np.pi * frequency * t) + np.random.normal(0, noise_level, n_samples)
    y = np.sin(2 * np.pi * frequency * t + np.pi / 4) + np.random.normal(0, noise_level, n_samples)
    z = np.sin(2 * np.pi * frequency * t + np.pi / 2) + np.random.normal(0, noise_level, n_samples)
    
    return np.column_stack([x, y, z])


# Pseudocode for edge device implementation (C++ / MicroPython)
"""
Edge Device Pseudocode (for reference):

void extract_features(float* accel_data, int n_samples, float* features) {
    // Window size: 1024 samples
    // Overlap: 75%
    int window_size = 1024;
    int step = 256;
    
    for (int i = 0; i < n_samples - window_size; i += step) {
        // Extract window
        float window_x[window_size];
        float window_y[window_size];
        float window_z[window_size];
        
        for (int j = 0; j < window_size; j++) {
            window_x[j] = accel_data[(i + j) * 3 + 0];
            window_y[j] = accel_data[(i + j) * 3 + 1];
            window_z[j] = accel_data[(i + j) * 3 + 2];
        }
        
        // Compute RMS
        float rms_x = compute_rms(window_x, window_size);
        float rms_y = compute_rms(window_y, window_size);
        float rms_z = compute_rms(window_z, window_size);
        
        // Compute peak
        float peak_x = compute_peak(window_x, window_size);
        float peak_y = compute_peak(window_y, window_size);
        float peak_z = compute_peak(window_z, window_size);
        
        // Store features
        features[0] = rms_x;
        features[1] = rms_y;
        features[2] = rms_z;
        features[3] = peak_x;
        features[4] = peak_y;
        features[5] = peak_z;
        // ... more features
    }
}

float compute_rms(float* data, int n) {
    float sum_sq = 0.0;
    for (int i = 0; i < n; i++) {
        sum_sq += data[i] * data[i];
    }
    return sqrt(sum_sq / n);
}
"""

