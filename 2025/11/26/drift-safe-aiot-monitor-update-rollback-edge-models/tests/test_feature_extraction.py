"""Tests for feature extraction module."""

import pytest
import numpy as np
from src.feature_extraction import (
    VibrationFeatureExtractor,
    simulate_accelerometer_data
)


def test_feature_extractor_init():
    """Test feature extractor initialization."""
    extractor = VibrationFeatureExtractor(window_size=1024, overlap=0.75)
    
    assert extractor.window_size == 1024
    assert extractor.overlap == 0.75
    assert extractor.step_size == 256  # 1024 * (1 - 0.75)


def test_feature_extraction():
    """Test feature extraction from accelerometer data."""
    extractor = VibrationFeatureExtractor(window_size=1024, overlap=0.75)
    
    # Generate test data
    accel_data = simulate_accelerometer_data(n_samples=5000, sample_rate=1000.0)
    
    # Extract features
    features = extractor.extract_features(accel_data)
    
    # Check output shape
    assert features.shape[0] > 0  # At least one window
    assert features.shape[1] == 9  # 3 axes × 3 features (RMS, peak, kurtosis)
    
    # Check feature values are reasonable
    assert np.all(np.isfinite(features))
    assert np.all(features >= 0)  # RMS and peak should be non-negative


def test_feature_stats_computation():
    """Test feature statistics computation."""
    extractor = VibrationFeatureExtractor(window_size=1024, overlap=0.75)
    
    # Generate test data
    accel_data = simulate_accelerometer_data(n_samples=5000, sample_rate=1000.0)
    features = extractor.extract_features(accel_data)
    
    # Compute stats
    stats = extractor.compute_feature_stats(features)
    
    # Check stats structure
    assert len(stats) == 9  # 9 features
    
    # Check each stat has required fields
    for feat_name, feat_stats in stats.items():
        assert hasattr(feat_stats, 'mean')
        assert hasattr(feat_stats, 'std')
        assert hasattr(feat_stats, 'min')
        assert hasattr(feat_stats, 'max')
        assert hasattr(feat_stats, 'p25')
        assert hasattr(feat_stats, 'p50')
        assert hasattr(feat_stats, 'p75')
        assert hasattr(feat_stats, 'p95')
        
        # Check ordering
        assert feat_stats.min <= feat_stats.p25 <= feat_stats.p50 <= feat_stats.p75 <= feat_stats.p95 <= feat_stats.max


def test_accelerometer_simulation():
    """Test accelerometer data simulation."""
    data = simulate_accelerometer_data(
        n_samples=1000,
        sample_rate=1000.0,
        frequency=50.0,
        noise_level=0.1
    )
    
    assert data.shape == (1000, 3)  # 3 axes
    assert np.all(np.isfinite(data))
    
    # Check reasonable range (depends on simulation parameters)
    assert np.abs(data).max() < 10.0  # Should be reasonable for vibration


def test_kurtosis_computation():
    """Test kurtosis computation."""
    extractor = VibrationFeatureExtractor()
    
    # Normal distribution should have kurtosis near 0
    normal_data = np.random.normal(0, 1, 1000)
    kurtosis = extractor._compute_kurtosis(normal_data)
    
    # Should be close to 0 (excess kurtosis)
    assert abs(kurtosis) < 1.0

