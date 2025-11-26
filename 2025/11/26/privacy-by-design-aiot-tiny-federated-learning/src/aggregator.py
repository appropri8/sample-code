"""Federated Learning Aggregation Methods

Implements FedAvg and other aggregation algorithms.
"""

import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional


class FedAvgAggregator:
    """Federated Averaging Aggregator
    
    Implements the standard FedAvg algorithm:
    - Average client updates weighted by number of local samples
    """
    
    def aggregate(
        self,
        updates: List[Dict[str, Any]],
        global_model_state: Optional[Dict[str, torch.Tensor]] = None
    ) -> Dict[str, torch.Tensor]:
        """Aggregate client updates using FedAvg
        
        Args:
            updates: List of updates from clients, each containing:
                - 'weights': weight deltas or full weights
                - 'num_samples': number of local training samples
            global_model_state: Current global model state (if updates are deltas)
            
        Returns:
            Aggregated model state dict
        """
        if not updates:
            raise ValueError("No updates to aggregate")
        
        # Get total number of samples
        total_samples = sum(u.get('num_samples', 1) for u in updates)
        
        # Initialize aggregated weights
        first_update = updates[0]['weights']
        aggregated = {}
        
        for key in first_update.keys():
            aggregated[key] = torch.zeros_like(first_update[key])
        
        # Weighted average
        for update in updates:
            weights = update['weights']
            num_samples = update.get('num_samples', 1)
            weight = num_samples / total_samples
            
            for key in weights.keys():
                aggregated[key] += weight * weights[key].float()
        
        # If updates are deltas, add to global model
        if global_model_state is not None:
            for key in aggregated.keys():
                aggregated[key] = global_model_state[key] + aggregated[key]
        
        return aggregated


class MedianAggregator:
    """Median Aggregator
    
    More robust to outliers (e.g., malicious clients).
    Takes median of updates instead of mean.
    """
    
    def aggregate(
        self,
        updates: List[Dict[str, Any]],
        global_model_state: Optional[Dict[str, torch.Tensor]] = None
    ) -> Dict[str, torch.Tensor]:
        """Aggregate using median
        
        Args:
            updates: List of client updates
            global_model_state: Current global model state
            
        Returns:
            Aggregated model state dict
        """
        if not updates:
            raise ValueError("No updates to aggregate")
        
        first_update = updates[0]['weights']
        aggregated = {}
        
        for key in first_update.keys():
            # Stack all updates for this layer
            stacked = torch.stack([u['weights'][key].float() for u in updates])
            # Take median along client dimension
            aggregated[key], _ = torch.median(stacked, dim=0)
        
        if global_model_state is not None:
            for key in aggregated.keys():
                aggregated[key] = global_model_state[key] + aggregated[key]
        
        return aggregated

