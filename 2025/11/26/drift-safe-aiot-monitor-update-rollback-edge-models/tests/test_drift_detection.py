"""Tests for drift detection module."""

import pytest
import numpy as np
import pandas as pd
from src.drift_detection import DriftDetector, DriftResult, compute_psi


def test_drift_detector_no_drift():
    """Test drift detector with no drift."""
    detector = DriftDetector()
    
    # Generate similar distributions
    baseline = pd.DataFrame({
        'feature1': np.random.normal(2.5, 0.3, 1000),
        'feature2': np.random.normal(1.8, 0.2, 1000)
    })
    
    recent = pd.DataFrame({
        'feature1': np.random.normal(2.5, 0.3, 200),
        'feature2': np.random.normal(1.8, 0.2, 200)
    })
    
    result = detector.detect_drift(baseline, recent, 'feature1')
    
    # Should not detect drift for similar distributions
    # (Note: KS test might still flag small differences, so we check p-value)
    assert result.ks_p_value > 0.01  # Very lenient threshold
    assert result.mean_shift_sigma < 1.0


def test_drift_detector_mean_shift():
    """Test drift detector with mean shift."""
    detector = DriftDetector()
    
    # Baseline: mean = 2.5
    baseline = pd.DataFrame({
        'feature1': np.random.normal(2.5, 0.3, 1000)
    })
    
    # Recent: mean = 3.5 (shifted by ~3.3 sigma)
    recent = pd.DataFrame({
        'feature1': np.random.normal(3.5, 0.3, 200)
    })
    
    result = detector.detect_drift(baseline, recent, 'feature1')
    
    # Should detect drift
    assert result.drift_detected
    assert result.mean_shift_sigma > 2.0
    assert result.drift_type == "mean_shift" or result.drift_type == "distribution_shift"


def test_drift_detector_from_stats():
    """Test drift detection from pre-computed statistics."""
    detector = DriftDetector()
    
    baseline_stats = {
        'feature1': {
            'mean': 2.5,
            'std': 0.3,
            'min': 2.0,
            'max': 3.1
        }
    }
    
    # Recent stats with mean shift
    recent_stats = {
        'feature1': {
            'mean': 3.5,  # Shifted
            'std': 0.3,
            'min': 2.5,
            'max': 4.0
        }
    }
    
    result = detector.detect_drift_from_stats(recent_stats, baseline_stats, 'feature1')
    
    # Should detect drift
    assert result.drift_detected
    assert result.mean_shift_sigma > 2.0


def test_compute_psi():
    """Test Population Stability Index computation."""
    # Similar distributions
    expected = np.random.normal(2.5, 0.3, 1000)
    actual = np.random.normal(2.5, 0.3, 1000)
    
    psi = compute_psi(expected, actual)
    
    # PSI should be low for similar distributions
    assert psi < 0.1
    
    # Different distributions
    actual_different = np.random.normal(3.5, 0.3, 1000)
    psi_different = compute_psi(expected, actual_different)
    
    # PSI should be higher for different distributions
    assert psi_different > psi


def test_feature_stats_computation():
    """Test feature statistics computation."""
    detector = DriftDetector()
    
    data = pd.DataFrame({
        'feature1': np.random.normal(2.5, 0.3, 1000)
    })
    
    stats = detector.compute_feature_stats(data, 'feature1')
    
    assert 'mean' in stats
    assert 'std' in stats
    assert 'min' in stats
    assert 'max' in stats
    assert 'p25' in stats
    assert 'p50' in stats
    assert 'p75' in stats
    assert 'p95' in stats
    
    assert stats['mean'] > 0
    assert stats['std'] > 0
    assert stats['min'] < stats['max']
    assert stats['p25'] < stats['p50'] < stats['p75'] < stats['p95']

