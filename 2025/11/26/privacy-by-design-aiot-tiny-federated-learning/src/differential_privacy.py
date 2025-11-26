"""Differential Privacy Utilities

Add noise to updates for privacy protection.
"""

import torch
import numpy as np
from typing import Dict, Any


def clip_gradients(
    update: Dict[str, torch.Tensor],
    max_norm: float = 1.0
) -> Dict[str, torch.Tensor]:
    """Clip gradients to maximum norm
    
    Args:
        update: Dictionary of weight updates
        max_norm: Maximum gradient norm
        
    Returns:
        Clipped updates
    """
    # Compute total norm
    total_norm = 0.0
    for key, weights in update.items():
        param_norm = weights.data.norm(2)
        total_norm += param_norm.item() ** 2
    total_norm = total_norm ** 0.5
    
    # Clip if needed
    clip_coef = max_norm / (total_norm + 1e-6)
    if clip_coef < 1.0:
        clipped = {}
        for key, weights in update.items():
            clipped[key] = weights * clip_coef
        return clipped
    
    return update


def add_dp_noise(
    update: Dict[str, torch.Tensor],
    epsilon: float = 1.0,
    delta: float = 1e-5,
    sensitivity: float = 1.0,
    clip_norm: float = 1.0
) -> Dict[str, torch.Tensor]:
    """Add differential privacy noise to update
    
    Args:
        update: Dictionary of weight updates
        epsilon: Privacy budget (epsilon)
        delta: Privacy parameter (delta)
        sensitivity: Maximum change from one data point
        clip_norm: Maximum norm for clipping
        
    Returns:
        Noisy updates
    """
    # First clip gradients
    clipped = clip_gradients(update, max_norm=clip_norm)
    
    # Compute noise scale
    # For Gaussian mechanism: sigma = sensitivity * sqrt(2*ln(1.25/delta)) / epsilon
    sigma = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
    
    # Add noise to each layer
    noisy = {}
    for key, weights in clipped.items():
        noise = torch.randn_like(weights) * sigma
        noisy[key] = weights + noise
    
    return noisy


class PrivacyBudget:
    """Track privacy budget usage"""
    
    def __init__(self, total_epsilon: float = 10.0):
        """Initialize privacy budget
        
        Args:
            total_epsilon: Total privacy budget
        """
        self.total_epsilon = total_epsilon
        self.used_epsilon = 0.0
    
    def can_participate(self, round_epsilon: float = 1.0) -> bool:
        """Check if device can participate in round
        
        Args:
            round_epsilon: Privacy cost for this round
            
        Returns:
            True if budget allows participation
        """
        return self.used_epsilon + round_epsilon <= self.total_epsilon
    
    def use(self, epsilon: float) -> None:
        """Use privacy budget
        
        Args:
            epsilon: Amount of budget to use
        """
        if self.used_epsilon + epsilon > self.total_epsilon:
            raise ValueError("Privacy budget exceeded")
        self.used_epsilon += epsilon
    
    def remaining(self) -> float:
        """Get remaining privacy budget
        
        Returns:
            Remaining epsilon
        """
        return self.total_epsilon - self.used_epsilon

