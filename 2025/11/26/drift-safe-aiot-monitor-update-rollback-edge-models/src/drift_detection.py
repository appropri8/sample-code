"""
Cloud-side drift detection for AIoT devices.

Compares recent telemetry windows to historical baselines using
statistical tests (KS test, PSI) and threshold checks.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DriftResult:
    """Result of drift detection for a feature."""
    feature_name: str
    drift_detected: bool
    ks_statistic: float
    ks_p_value: float
    mean_shift_sigma: float
    variance_ratio: float
    drift_type: Optional[str] = None
    severity: str = "low"  # low, medium, high


class DriftDetector:
    """
    Detects drift in feature distributions by comparing recent data to baseline.
    
    Uses:
    - Kolmogorov-Smirnov test for distribution shifts
    - Mean shift detection (sigma-based)
    - Variance ratio for spread changes
    """
    
    def __init__(self, baseline_window_days: int = 30, recent_window_days: int = 7):
        """
        Initialize drift detector.
        
        Args:
            baseline_window_days: Days of historical data to use as baseline
            recent_window_days: Days of recent data to compare against baseline
        """
        self.baseline_window_days = baseline_window_days
        self.recent_window_days = recent_window_days
        self.ks_threshold = 0.05  # p-value threshold for KS test
        self.mean_shift_threshold = 2.0  # sigma threshold for mean shift
        self.variance_ratio_threshold_high = 1.5
        self.variance_ratio_threshold_low = 0.67
    
    def detect_drift(
        self,
        recent_data: pd.DataFrame,
        baseline_data: pd.DataFrame,
        feature_name: str
    ) -> DriftResult:
        """
        Detect drift for a single feature.
        
        Args:
            recent_data: DataFrame with recent feature values
            baseline_data: DataFrame with baseline feature values
            feature_name: Name of the feature to check
        
        Returns:
            DriftResult with drift detection results
        """
        recent_values = recent_data[feature_name].dropna().values
        baseline_values = baseline_data[feature_name].dropna().values
        
        if len(recent_values) == 0 or len(baseline_values) == 0:
            return DriftResult(
                feature_name=feature_name,
                drift_detected=False,
                ks_statistic=0.0,
                ks_p_value=1.0,
                mean_shift_sigma=0.0,
                variance_ratio=1.0,
                drift_type="insufficient_data"
            )
        
        # Kolmogorov-Smirnov test
        ks_stat, ks_p_value = stats.ks_2samp(baseline_values, recent_values)
        
        # Mean shift
        baseline_mean = np.mean(baseline_values)
        baseline_std = np.std(baseline_values)
        recent_mean = np.mean(recent_values)
        mean_shift_sigma = abs(recent_mean - baseline_mean) / baseline_std if baseline_std > 0 else 0.0
        
        # Variance ratio
        baseline_variance = np.var(baseline_values)
        recent_variance = np.var(recent_values)
        variance_ratio = recent_variance / baseline_variance if baseline_variance > 0 else 1.0
        
        # Determine drift
        drift_detected = (
            ks_p_value < self.ks_threshold or
            mean_shift_sigma > self.mean_shift_threshold or
            variance_ratio > self.variance_ratio_threshold_high or
            variance_ratio < self.variance_ratio_threshold_low
        )
        
        # Determine drift type
        drift_type = None
        if drift_detected:
            if ks_p_value < self.ks_threshold:
                drift_type = "distribution_shift"
            elif mean_shift_sigma > self.mean_shift_threshold:
                drift_type = "mean_shift"
            elif variance_ratio > self.variance_ratio_threshold_high or variance_ratio < self.variance_ratio_threshold_low:
                drift_type = "variance_shift"
        
        # Determine severity
        severity = "low"
        if drift_detected:
            if mean_shift_sigma > 3.0 or variance_ratio > 2.0 or variance_ratio < 0.5:
                severity = "high"
            elif mean_shift_sigma > 2.5 or variance_ratio > 1.75 or variance_ratio < 0.6:
                severity = "medium"
        
        return DriftResult(
            feature_name=feature_name,
            drift_detected=drift_detected,
            ks_statistic=ks_stat,
            ks_p_value=ks_p_value,
            mean_shift_sigma=mean_shift_sigma,
            variance_ratio=variance_ratio,
            drift_type=drift_type,
            severity=severity
        )
    
    def detect_drift_from_stats(
        self,
        recent_stats: Dict[str, Dict[str, float]],
        baseline_stats: Dict[str, Dict[str, float]],
        feature_name: str
    ) -> DriftResult:
        """
        Detect drift using pre-computed statistics (for low-bandwidth scenarios).
        
        Args:
            recent_stats: Dict with recent feature statistics
            baseline_stats: Dict with baseline feature statistics
            feature_name: Name of the feature to check
        
        Returns:
            DriftResult with drift detection results
        """
        if feature_name not in recent_stats or feature_name not in baseline_stats:
            return DriftResult(
                feature_name=feature_name,
                drift_detected=False,
                ks_statistic=0.0,
                ks_p_value=1.0,
                mean_shift_sigma=0.0,
                variance_ratio=1.0,
                drift_type="missing_data"
            )
        
        recent = recent_stats[feature_name]
        baseline = baseline_stats[feature_name]
        
        # Mean shift
        baseline_mean = baseline.get('mean', 0.0)
        baseline_std = baseline.get('std', 1.0)
        recent_mean = recent.get('mean', 0.0)
        mean_shift_sigma = abs(recent_mean - baseline_mean) / baseline_std if baseline_std > 0 else 0.0
        
        # Variance ratio (using std^2 as variance proxy)
        baseline_variance = baseline.get('std', 1.0) ** 2
        recent_variance = recent.get('std', 1.0) ** 2
        variance_ratio = recent_variance / baseline_variance if baseline_variance > 0 else 1.0
        
        # Range check (simple threshold-based drift)
        baseline_min = baseline.get('min', 0.0)
        baseline_max = baseline.get('max', 0.0)
        recent_min = recent.get('min', 0.0)
        recent_max = recent.get('max', 0.0)
        
        range_shift = (
            recent_min < baseline_min * 0.9 or
            recent_max > baseline_max * 1.1
        )
        
        # Determine drift
        drift_detected = (
            mean_shift_sigma > self.mean_shift_threshold or
            variance_ratio > self.variance_ratio_threshold_high or
            variance_ratio < self.variance_ratio_threshold_low or
            range_shift
        )
        
        # Determine drift type
        drift_type = None
        if drift_detected:
            if mean_shift_sigma > self.mean_shift_threshold:
                drift_type = "mean_shift"
            elif variance_ratio > self.variance_ratio_threshold_high or variance_ratio < self.variance_ratio_threshold_low:
                drift_type = "variance_shift"
            elif range_shift:
                drift_type = "range_shift"
        
        # Determine severity
        severity = "low"
        if drift_detected:
            if mean_shift_sigma > 3.0 or variance_ratio > 2.0 or variance_ratio < 0.5:
                severity = "high"
            elif mean_shift_sigma > 2.5 or variance_ratio > 1.75 or variance_ratio < 0.6:
                severity = "medium"
        
        return DriftResult(
            feature_name=feature_name,
            drift_detected=drift_detected,
            ks_statistic=0.0,  # Not available from stats
            ks_p_value=1.0,  # Not available from stats
            mean_shift_sigma=mean_shift_sigma,
            variance_ratio=variance_ratio,
            drift_type=drift_type,
            severity=severity
        )
    
    def compute_feature_stats(self, data: pd.DataFrame, feature_name: str) -> Dict[str, float]:
        """
        Compute statistics for a feature (for telemetry compression).
        
        Args:
            data: DataFrame with feature values
            feature_name: Name of the feature
        
        Returns:
            Dict with mean, std, min, max, percentiles
        """
        values = data[feature_name].dropna().values
        
        if len(values) == 0:
            return {
                'mean': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'p25': 0.0,
                'p50': 0.0,
                'p75': 0.0,
                'p95': 0.0
            }
        
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'p25': float(np.percentile(values, 25)),
            'p50': float(np.percentile(values, 50)),
            'p75': float(np.percentile(values, 75)),
            'p95': float(np.percentile(values, 95))
        }


def compute_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """
    Compute Population Stability Index (PSI) between two distributions.
    
    PSI < 0.1: No significant change
    PSI 0.1-0.25: Minor change
    PSI > 0.25: Significant change
    
    Args:
        expected: Baseline distribution
        actual: Recent distribution
        bins: Number of bins for histogram
    
    Returns:
        PSI value
    """
    # Create bins based on expected distribution
    min_val = min(np.min(expected), np.min(actual))
    max_val = max(np.max(expected), np.max(actual))
    bin_edges = np.linspace(min_val, max_val, bins + 1)
    
    # Compute histograms
    expected_hist, _ = np.histogram(expected, bins=bin_edges)
    actual_hist, _ = np.histogram(actual, bins=bin_edges)
    
    # Normalize to probabilities
    expected_prob = expected_hist / len(expected)
    actual_prob = actual_hist / len(actual)
    
    # Avoid division by zero
    expected_prob = np.where(expected_prob == 0, 1e-10, expected_prob)
    actual_prob = np.where(actual_prob == 0, 1e-10, actual_prob)
    
    # Compute PSI
    psi = np.sum((actual_prob - expected_prob) * np.log(actual_prob / expected_prob))
    
    return float(psi)

