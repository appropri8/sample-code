"""Metrics calculation for feedback data"""

from typing import List, Dict, Any
from statistics import median


def calculate_task_success_rate(feedback_data: List[Dict[str, Any]]) -> float:
    """Calculate percentage of successful tasks."""
    if not feedback_data:
        return 0.0
    
    successful = sum(
        1 for f in feedback_data
        if f.get("feedback_value", {}).get("task_succeeded", False)
    )
    return successful / len(feedback_data)


def calculate_human_help_rate(feedback_data: List[Dict[str, Any]]) -> float:
    """Calculate percentage of cases needing human help."""
    if not feedback_data:
        return 0.0
    
    needed_help = sum(
        1 for f in feedback_data
        if f.get("feedback_value", {}).get("needed_human_help", False)
    )
    return needed_help / len(feedback_data)


def calculate_safety_trigger_rate(feedback_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate safety filter trigger rates."""
    triggers = {"high": 0, "medium": 0, "low": 0}
    total = len(feedback_data)
    
    if total == 0:
        return {level: 0.0 for level in triggers.keys()}
    
    for f in feedback_data:
        safety_level = f.get("feedback_value", {}).get("safety_filter_level")
        if safety_level and safety_level in triggers:
            triggers[safety_level] += 1
    
    return {
        level: count / total
        for level, count in triggers.items()
    }


def calculate_latency_percentiles(feedback_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate latency percentiles."""
    latencies = [
        f.get("metadata", {}).get("latency_ms", 0)
        for f in feedback_data
        if f.get("metadata", {}).get("latency_ms")
    ]
    
    if not latencies:
        return {}
    
    latencies.sort()
    n = len(latencies)
    
    return {
        "p50": latencies[int(n * 0.50)] if n > 0 else 0,
        "p95": latencies[int(n * 0.95)] if n > 1 else latencies[0],
        "p99": latencies[int(n * 0.99)] if n > 1 else latencies[0]
    }


def calculate_cost_per_success(feedback_data: List[Dict[str, Any]]) -> float:
    """Calculate average cost per successful task."""
    total_cost = sum(
        f.get("metadata", {}).get("cost_estimate", 0)
        for f in feedback_data
    )
    
    successful_tasks = sum(
        1 for f in feedback_data
        if f.get("feedback_value", {}).get("task_succeeded", False)
    )
    
    return total_cost / successful_tasks if successful_tasks > 0 else 0.0


def compare_prompt_versions(feedback_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Compare metrics across prompt versions."""
    versions = {}
    
    # Group by prompt version
    for f in feedback_data:
        version = f.get("prompt_version", "unknown")
        if version not in versions:
            versions[version] = []
        versions[version].append(f)
    
    # Calculate metrics for each version
    results = {}
    for version, data in versions.items():
        results[version] = {
            "task_success_rate": calculate_task_success_rate(data),
            "human_help_rate": calculate_human_help_rate(data),
            "safety_triggers": calculate_safety_trigger_rate(data),
            "latency_percentiles": calculate_latency_percentiles(data),
            "cost_per_success": calculate_cost_per_success(data),
            "sample_size": len(data)
        }
    
    return results


def calculate_edit_ratio_avg(feedback_data: List[Dict[str, Any]]) -> float:
    """Calculate average edit ratio (implicit feedback)."""
    edit_ratios = [
        f.get("feedback_value", {}).get("edit_ratio", 0)
        for f in feedback_data
        if f.get("feedback_value", {}).get("edit_ratio") is not None
    ]
    
    return sum(edit_ratios) / len(edit_ratios) if edit_ratios else 0.0


def calculate_abandonment_rate(feedback_data: List[Dict[str, Any]]) -> float:
    """Calculate abandonment rate (implicit feedback)."""
    if not feedback_data:
        return 0.0
    
    abandoned = sum(
        1 for f in feedback_data
        if f.get("feedback_value", {}).get("abandoned", False)
    )
    return abandoned / len(feedback_data)

