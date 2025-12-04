"""Shadow deployment for comparing baseline and candidate workflows"""
from typing import Dict, Any, List
import logging
from datetime import datetime


class ShadowDeployment:
    """Shadow deployment: mirror traffic and compare"""
    
    def __init__(
        self,
        baseline_workflow,
        candidate_workflow,
        comparison_metrics: List[str] = None
    ):
        self.baseline = baseline_workflow
        self.candidate = candidate_workflow
        self.metrics = comparison_metrics or [
            "latency_ms",
            "tokens_used",
            "cost",
            "tools_called",
            "success"
        ]
        self.logger = logging.getLogger(__name__)
        self.comparisons = []
    
    def run_shadow(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Run both workflows and compare"""
        # Run baseline (production)
        baseline_result = self.baseline.execute(input)
        
        # Run candidate (shadow)
        candidate_result = self.candidate.execute(input)
        
        # Compare
        comparison = self._compare_results(
            baseline_result,
            candidate_result
        )
        
        # Store comparison
        self.comparisons.append({
            "timestamp": datetime.utcnow().isoformat(),
            "input": input,
            "baseline": baseline_result,
            "candidate": candidate_result,
            "comparison": comparison
        })
        
        # Log everything
        self.logger.info({
            "input": input,
            "baseline": baseline_result,
            "candidate": candidate_result,
            "comparison": comparison
        })
        
        # Return baseline result (candidate doesn't affect users)
        return baseline_result
    
    def _compare_results(
        self,
        baseline: Dict[str, Any],
        candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare baseline and candidate results"""
        comparison = {}
        
        for metric in self.metrics:
            baseline_val = baseline.get(metric)
            candidate_val = candidate.get(metric)
            
            if baseline_val is None or candidate_val is None:
                comparison[metric] = "missing"
            elif isinstance(baseline_val, (int, float)) and isinstance(candidate_val, (int, float)):
                diff = abs(baseline_val - candidate_val)
                pct_diff = (diff / baseline_val) * 100 if baseline_val != 0 else 0
                comparison[metric] = {
                    "baseline": baseline_val,
                    "candidate": candidate_val,
                    "diff": diff,
                    "pct_diff": pct_diff
                }
            elif isinstance(baseline_val, list) and isinstance(candidate_val, list):
                comparison[metric] = {
                    "baseline": baseline_val,
                    "candidate": candidate_val,
                    "match": set(baseline_val) == set(candidate_val)
                }
            else:
                comparison[metric] = {
                    "baseline": baseline_val,
                    "candidate": candidate_val,
                    "match": baseline_val == candidate_val
                }
        
        return comparison
    
    def get_comparison_summary(self) -> Dict[str, Any]:
        """Get summary of all comparisons"""
        if not self.comparisons:
            return {}
        
        summary = {
            "total_comparisons": len(self.comparisons),
            "metrics": {}
        }
        
        for metric in self.metrics:
            metric_values = []
            for comp in self.comparisons:
                comp_data = comp["comparison"].get(metric, {})
                if isinstance(comp_data, dict) and "pct_diff" in comp_data:
                    metric_values.append(comp_data["pct_diff"])
            
            if metric_values:
                summary["metrics"][metric] = {
                    "avg_pct_diff": sum(metric_values) / len(metric_values),
                    "max_pct_diff": max(metric_values),
                    "min_pct_diff": min(metric_values)
                }
        
        return summary

