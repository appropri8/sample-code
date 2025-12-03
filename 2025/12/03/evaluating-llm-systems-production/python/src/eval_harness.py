"""
Evaluation harness for running golden set against models.
"""

import json
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class EvaluationResult:
    """Result for a single evaluation example."""
    example_id: str
    baseline_output: str
    candidate_output: str
    baseline_labels: Optional[Dict[str, str]] = None
    candidate_labels: Optional[Dict[str, str]] = None
    metrics: Optional[Dict[str, float]] = None


class EvaluationHarness:
    """Evaluation harness for comparing models."""
    
    def __init__(self, golden_set_path: str):
        """Initialize with path to golden set."""
        self.golden_set_path = golden_set_path
        self.golden_set = self._load_golden_set()
    
    def _load_golden_set(self) -> List[Dict]:
        """Load golden set from file."""
        with open(self.golden_set_path) as f:
            return json.load(f)
    
    def run_evaluation(
        self,
        baseline_model: Callable[[str], str],
        candidate_model: Callable[[str], str],
        labeler: Optional[Callable[[str, str, str, Optional[str]], Dict[str, str]]] = None
    ) -> List[EvaluationResult]:
        """
        Run evaluation on golden set.
        
        Args:
            baseline_model: Function that takes input query and returns output
            candidate_model: Function that takes input query and returns output
            labeler: Optional function to label outputs (input, output_a, output_b, expected_behavior) -> labels
        """
        results = []
        
        for example in self.golden_set:
            example_id = example.get("id", f"example_{len(results)}")
            input_query = example["input"].get("query", "")
            expected_behavior = example.get("expected_behavior")
            
            # Run baseline
            baseline_output = baseline_model(input_query)
            
            # Run candidate
            candidate_output = candidate_model(input_query)
            
            # Label if labeler provided
            baseline_labels = None
            candidate_labels = None
            if labeler:
                baseline_labels = labeler(input_query, baseline_output, expected_behavior, "baseline")
                candidate_labels = labeler(input_query, candidate_output, expected_behavior, "candidate")
            
            # Compute metrics
            metrics = self._compute_metrics(baseline_labels, candidate_labels) if baseline_labels and candidate_labels else None
            
            results.append(EvaluationResult(
                example_id=example_id,
                baseline_output=baseline_output,
                candidate_output=candidate_output,
                baseline_labels=baseline_labels,
                candidate_labels=candidate_labels,
                metrics=metrics
            ))
        
        return results
    
    def _compute_metrics(
        self,
        baseline_labels: Dict[str, str],
        candidate_labels: Dict[str, str]
    ) -> Dict[str, float]:
        """Compute metrics comparing baseline and candidate labels."""
        metrics = {}
        
        for key in set(baseline_labels.keys()) | set(candidate_labels.keys()):
            baseline_value = baseline_labels.get(key, "unknown")
            candidate_value = candidate_labels.get(key, "unknown")
            
            # Both correct
            if baseline_value == "correct" and candidate_value == "correct":
                metrics[f"{key}_both_correct"] = 1.0
            # Candidate improved
            elif baseline_value != "correct" and candidate_value == "correct":
                metrics[f"{key}_improved"] = 1.0
            # Candidate regressed
            elif baseline_value == "correct" and candidate_value != "correct":
                metrics[f"{key}_regressed"] = 1.0
            # Both wrong
            else:
                metrics[f"{key}_both_wrong"] = 1.0
        
        return metrics
    
    def print_results(self, results: List[EvaluationResult]):
        """Print evaluation results in a readable format."""
        total = len(results)
        
        print(f"\n{'='*60}")
        print(f"Evaluation Results ({total} examples)")
        print(f"{'='*60}\n")
        
        # Aggregate metrics
        aggregated = {}
        for result in results:
            if result.metrics:
                for key, value in result.metrics.items():
                    aggregated[key] = aggregated.get(key, 0) + value
        
        # Print aggregated metrics
        if aggregated:
            print("Aggregated Metrics:")
            for key, count in sorted(aggregated.items()):
                percentage = (count / total) * 100
                print(f"  {key}: {count}/{total} ({percentage:.1f}%)")
        
        # Print per-example results
        print(f"\nPer-Example Results:")
        for result in results[:10]:  # Show first 10
            print(f"\n  Example: {result.example_id}")
            if result.baseline_labels and result.candidate_labels:
                print(f"    Baseline: {result.baseline_labels}")
                print(f"    Candidate: {result.candidate_labels}")
        
        if len(results) > 10:
            print(f"\n  ... and {len(results) - 10} more examples")
    
    def check_regressions(
        self,
        results: List[EvaluationResult],
        min_pass_rate: float = 0.95
    ) -> bool:
        """Check if candidate has regressions."""
        total = len(results)
        regressions = 0
        
        for result in results:
            if result.metrics:
                for key, value in result.metrics.items():
                    if "regressed" in key and value > 0:
                        regressions += 1
                        break
        
        pass_rate = 1.0 - (regressions / total) if total > 0 else 0.0
        
        if pass_rate < min_pass_rate:
            print(f"FAILED: Pass rate {pass_rate:.2%} below threshold {min_pass_rate:.2%}")
            return False
        
        print(f"PASSED: Pass rate {pass_rate:.2%}")
        return True

