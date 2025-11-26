"""
Example: Cloud-side drift detection.

Reads historical vs recent feature data and computes drift scores.
Prints go/no-go flag for retraining.
"""

import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.drift_detection import DriftDetector, DriftResult


def load_feature_data(file_path: str) -> pd.DataFrame:
    """Load feature data from CSV."""
    return pd.read_csv(file_path)


def detect_drift_from_files(
    recent_file: str,
    baseline_file: str,
    feature_names: list = None
) -> list:
    """
    Detect drift by comparing recent data to baseline.
    
    Args:
        recent_file: Path to recent feature data CSV
        baseline_file: Path to baseline feature data CSV
        feature_names: List of feature names to check (None = all)
    
    Returns:
        List of DriftResult objects
    """
    # Load data
    recent_data = load_feature_data(recent_file)
    baseline_data = load_feature_data(baseline_file)
    
    # Get feature names
    if feature_names is None:
        # Assume all columns except timestamp/device_id are features
        exclude_cols = ['timestamp', 'device_id', 'date', 'time']
        feature_names = [col for col in recent_data.columns if col not in exclude_cols]
    
    # Initialize detector
    detector = DriftDetector(baseline_window_days=30, recent_window_days=7)
    
    # Detect drift for each feature
    results = []
    for feature_name in feature_names:
        if feature_name not in recent_data.columns or feature_name not in baseline_data.columns:
            print(f"Warning: Feature '{feature_name}' not found in data")
            continue
        
        result = detector.detect_drift(recent_data, baseline_data, feature_name)
        results.append(result)
    
    return results


def print_drift_report(results: list):
    """Print drift detection report."""
    print("\n" + "=" * 80)
    print("DRIFT DETECTION REPORT")
    print("=" * 80)
    
    drift_detected = False
    
    for result in results:
        status = "DRIFT DETECTED" if result.drift_detected else "NO DRIFT"
        severity = result.severity.upper()
        
        print(f"\nFeature: {result.feature_name}")
        print(f"  Status: {status} ({severity})")
        
        if result.drift_detected:
            drift_detected = True
            print(f"  Type: {result.drift_type}")
            print(f"  KS p-value: {result.ks_p_value:.4f}")
            print(f"  Mean shift: {result.mean_shift_sigma:.2f}σ")
            print(f"  Variance ratio: {result.variance_ratio:.2f}")
    
    print("\n" + "=" * 80)
    
    if drift_detected:
        print("RECOMMENDATION: RETRAIN MODEL")
        return False  # Go flag
    else:
        print("RECOMMENDATION: NO ACTION NEEDED")
        return True  # No-go flag


def main():
    parser = argparse.ArgumentParser(description="Detect drift in feature data")
    parser.add_argument(
        '--recent',
        type=str,
        required=True,
        help='Path to recent feature data CSV'
    )
    parser.add_argument(
        '--baseline',
        type=str,
        required=True,
        help='Path to baseline feature data CSV'
    )
    parser.add_argument(
        '--features',
        type=str,
        nargs='+',
        help='Feature names to check (default: all)'
    )
    parser.add_argument(
        '--window-size',
        type=int,
        default=7,
        help='Recent window size in days (default: 7)'
    )
    
    args = parser.parse_args()
    
    # Detect drift
    results = detect_drift_from_files(args.recent, args.baseline, args.features)
    
    # Print report
    no_action_needed = print_drift_report(results)
    
    # Exit code: 0 = no action, 1 = retrain needed
    sys.exit(0 if no_action_needed else 1)


if __name__ == '__main__':
    main()

