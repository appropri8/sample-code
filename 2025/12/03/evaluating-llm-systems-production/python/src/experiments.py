"""
A/B testing and shadow testing for LLM systems.
"""

import hashlib
from typing import Callable, Optional, Dict
from dataclasses import dataclass


@dataclass
class ExperimentAssignment:
    """Result of experiment assignment."""
    variant: str  # "baseline" or "candidate"
    cohort: str  # "control" or "treatment"
    experiment_name: str


def assign_variant(
    user_id: str,
    experiment_name: str,
    split_ratio: float = 0.5
) -> str:
    """
    Deterministically assign user to variant.
    
    Args:
        user_id: User identifier
        experiment_name: Name of experiment
        split_ratio: Ratio for candidate (0.5 = 50/50 split)
    
    Returns: "baseline" or "candidate"
    """
    seed = f"{experiment_name}:{user_id}"
    hash_value = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    threshold = int(split_ratio * 100)
    return "candidate" if (hash_value % 100) < threshold else "baseline"


def assign_cohort(
    user_id: str,
    experiment_name: str
) -> str:
    """Assign user to cohort (control or treatment)."""
    variant = assign_variant(user_id, experiment_name)
    return "treatment" if variant == "candidate" else "control"


class ABTest:
    """A/B test manager."""
    
    def __init__(
        self,
        experiment_name: str,
        baseline_model: Callable[[str], str],
        candidate_model: Callable[[str], str],
        split_ratio: float = 0.5
    ):
        """Initialize A/B test."""
        self.experiment_name = experiment_name
        self.baseline_model = baseline_model
        self.candidate_model = candidate_model
        self.split_ratio = split_ratio
    
    def run(
        self,
        user_id: str,
        query: str
    ) -> tuple[str, ExperimentAssignment]:
        """
        Run query through A/B test.
        
        Returns: (output, assignment)
        """
        assignment = ExperimentAssignment(
            variant=assign_variant(user_id, self.experiment_name, self.split_ratio),
            cohort=assign_cohort(user_id, self.experiment_name),
            experiment_name=self.experiment_name
        )
        
        if assignment.variant == "baseline":
            output = self.baseline_model(query)
        else:
            output = self.candidate_model(query)
        
        return output, assignment


class ShadowTest:
    """Shadow test manager."""
    
    def __init__(
        self,
        experiment_name: str,
        baseline_model: Callable[[str], str],
        candidate_model: Callable[[str], str],
        logger: Optional[Callable] = None
    ):
        """Initialize shadow test."""
        self.experiment_name = experiment_name
        self.baseline_model = baseline_model
        self.candidate_model = candidate_model
        self.logger = logger
    
    def run(
        self,
        user_id: str,
        query: str
    ) -> tuple[str, Dict]:
        """
        Run shadow test.
        User sees baseline, candidate runs in background.
        
        Returns: (baseline_output, comparison_data)
        """
        # User sees baseline
        baseline_output = self.baseline_model(query)
        
        # Candidate runs in background (user doesn't see this)
        candidate_output = self.candidate_model(query)
        
        # Log comparison
        comparison_data = {
            "experiment_name": self.experiment_name,
            "user_id": user_id,
            "query": query,
            "baseline_output": baseline_output,
            "candidate_output": candidate_output
        }
        
        if self.logger:
            self.logger(comparison_data)
        
        return baseline_output, comparison_data

