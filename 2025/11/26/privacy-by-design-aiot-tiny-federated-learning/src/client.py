"""Federated Learning Client

Simulates a device that participates in federated learning.
"""

import copy
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Optional
from .quantization import quantize_weights


class FLClient:
    """Federated Learning Client
    
    Represents a device that:
    - Receives global model
    - Trains on local data
    - Sends weight updates back
    """
    
    def __init__(
        self,
        client_id: int,
        local_data: torch.utils.data.DataLoader,
        model: nn.Module,
        learning_rate: float = 0.01,
        use_quantization: bool = True,
        quantization_bits: int = 8
    ):
        """Initialize client
        
        Args:
            client_id: Unique identifier for this client
            local_data: DataLoader with local training data
            model: Initial model (will be updated with global model)
            learning_rate: Learning rate for local training
            use_quantization: Whether to quantize updates
            quantization_bits: Bits for quantization
        """
        self.client_id = client_id
        self.local_data = local_data
        self.model = model
        self.learning_rate = learning_rate
        self.use_quantization = use_quantization
        self.quantization_bits = quantization_bits
        
        self.global_model_state = None
        self.local_epochs = 3
        
    def receive_global_model(self, global_state: Dict[str, torch.Tensor]) -> None:
        """Receive global model from coordinator
        
        Args:
            global_state: State dict of global model
        """
        self.global_model_state = copy.deepcopy(global_state)
        self.model.load_state_dict(self.global_model_state)
    
    def train_locally(self, epochs: Optional[int] = None) -> None:
        """Train model on local data
        
        Args:
            epochs: Number of epochs (uses self.local_epochs if None)
        """
        if self.global_model_state is None:
            raise ValueError("Must receive global model before training")
        
        epochs = epochs or self.local_epochs
        
        # Set model to training mode
        self.model.train()
        
        # Create optimizer
        optimizer = optim.SGD(self.model.parameters(), lr=self.learning_rate)
        
        # Loss function (assuming classification)
        criterion = nn.CrossEntropyLoss()
        
        # Train for specified epochs
        for epoch in range(epochs):
            for batch_data, batch_labels in self.local_data:
                optimizer.zero_grad()
                
                # Forward pass
                outputs = self.model(batch_data)
                loss = criterion(outputs, batch_labels)
                
                # Backward pass
                loss.backward()
                optimizer.step()
    
    def compute_update(self) -> Dict[str, torch.Tensor]:
        """Compute weight update (difference from global model)
        
        Returns:
            Dictionary of weight deltas
        """
        if self.global_model_state is None:
            raise ValueError("Must receive global model before computing update")
        
        current_state = self.model.state_dict()
        update = {}
        
        for key in current_state:
            update[key] = current_state[key] - self.global_model_state[key]
        
        return update
    
    def send_update(self) -> Optional[Dict[str, Any]]:
        """Send update to coordinator
        
        Returns:
            Update dictionary with weights and metadata, or None if error
        """
        try:
            # Train locally
            self.train_locally()
            
            # Compute update
            update = self.compute_update()
            
            # Count local samples
            num_samples = sum(len(batch[0]) for batch in self.local_data)
            
            # Quantize if needed
            if self.use_quantization:
                quantized_update = {}
                scales = {}
                zero_points = {}
                
                for key, weights in update.items():
                    quantized, scale, zero_point = quantize_weights(
                        weights,
                        bits=self.quantization_bits
                    )
                    quantized_update[key] = quantized
                    scales[key] = scale
                    zero_points[key] = zero_point
                
                return {
                    'client_id': self.client_id,
                    'weights': quantized_update,
                    'scale': scales,
                    'zero_point': zero_points,
                    'num_samples': num_samples,
                    'quantized': True
                }
            else:
                return {
                    'client_id': self.client_id,
                    'weights': update,
                    'num_samples': num_samples,
                    'quantized': False
                }
        
        except Exception as e:
            print(f"Client {self.client_id} error: {e}")
            return None
    
    def get_model(self) -> nn.Module:
        """Get current model
        
        Returns:
            Current model
        """
        return self.model

