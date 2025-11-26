"""Federated Learning Coordinator

Manages FL rounds, device selection, and aggregation.
"""

import random
import copy
from typing import List, Dict, Any
import torch
import torch.nn as nn
from .aggregator import FedAvgAggregator
from .quantization import quantize_weights, dequantize_weights


class FLCoordinator:
    """Federated Learning Coordinator
    
    Manages the federated learning process:
    - Selects devices for each round
    - Sends global model to devices
    - Collects updates from devices
    - Aggregates updates
    - Updates global model
    """
    
    def __init__(
        self,
        num_clients: int = 10,
        clients_per_round: int = 5,
        local_epochs: int = 3,
        learning_rate: float = 0.01,
        use_quantization: bool = True,
        quantization_bits: int = 8,
        use_dp: bool = False,
        dp_epsilon: float = 1.0,
        dp_delta: float = 1e-5
    ):
        """Initialize coordinator
        
        Args:
            num_clients: Total number of clients in the system
            clients_per_round: Number of clients selected per round
            local_epochs: Number of local training epochs per client
            learning_rate: Learning rate for local training
            use_quantization: Whether to quantize weight updates
            quantization_bits: Bits for quantization (8 or 4)
            use_dp: Whether to use differential privacy
            dp_epsilon: Privacy budget (epsilon)
            dp_delta: Privacy parameter (delta)
        """
        self.num_clients = num_clients
        self.clients_per_round = clients_per_round
        self.local_epochs = local_epochs
        self.learning_rate = learning_rate
        self.use_quantization = use_quantization
        self.quantization_bits = quantization_bits
        self.use_dp = use_dp
        self.dp_epsilon = dp_epsilon
        self.dp_delta = dp_delta
        
        self.aggregator = FedAvgAggregator()
        self.round_history = []
        
    def select_clients(self, available_clients: List[Any]) -> List[Any]:
        """Select clients for this round
        
        Args:
            available_clients: List of available client objects
            
        Returns:
            Selected clients
        """
        # Simple random sampling
        # In practice, you might use stratified sampling, availability-based, etc.
        num_to_select = min(self.clients_per_round, len(available_clients))
        return random.sample(available_clients, num_to_select)
    
    def send_global_model(self, global_model: nn.Module, clients: List[Any]) -> None:
        """Send global model to selected clients
        
        Args:
            global_model: Current global model
            clients: List of client objects to send model to
        """
        global_state = global_model.state_dict()
        for client in clients:
            client.receive_global_model(copy.deepcopy(global_state))
    
    def collect_updates(
        self,
        clients: List[Any],
        timeout: int = 3600
    ) -> List[Dict[str, Any]]:
        """Collect updates from clients
        
        Args:
            clients: List of clients that should send updates
            timeout: Maximum time to wait for updates (seconds)
            
        Returns:
            List of updates, each containing weights and metadata
        """
        updates = []
        
        for client in clients:
            # In real system, this would be async with timeout
            update = client.send_update()
            
            if update is not None:
                # Dequantize if needed
                if self.use_quantization and 'quantized' in update:
                    weights = dequantize_weights(
                        update['weights'],
                        update['scale'],
                        update['zero_point']
                    )
                    update['weights'] = weights
                
                updates.append(update)
        
        return updates
    
    def run_round(
        self,
        global_model: nn.Module,
        available_clients: List[Any]
    ) -> nn.Module:
        """Run one federated learning round
        
        Args:
            global_model: Current global model
            available_clients: All available clients
            
        Returns:
            Updated global model
        """
        # 1. Select clients
        selected_clients = self.select_clients(available_clients)
        print(f"Selected {len(selected_clients)} clients for this round")
        
        # 2. Send global model
        self.send_global_model(global_model, selected_clients)
        
        # 3. Clients train locally (happens on client side)
        # This is simulated - in real system, clients would train asynchronously
        
        # 4. Collect updates
        updates = self.collect_updates(selected_clients)
        print(f"Collected {len(updates)} updates")
        
        if len(updates) == 0:
            print("No updates received, returning original model")
            return global_model
        
        # 5. Aggregate updates
        aggregated_weights = self.aggregator.aggregate(updates)
        
        # 6. Update global model
        global_model.load_state_dict(aggregated_weights)
        
        # 7. Record round metrics
        round_metrics = {
            'round_num': len(self.round_history) + 1,
            'clients_selected': len(selected_clients),
            'updates_received': len(updates),
            'avg_samples_per_client': sum(u.get('num_samples', 0) for u in updates) / len(updates) if updates else 0
        }
        self.round_history.append(round_metrics)
        
        return global_model
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get coordinator metrics
        
        Returns:
            Dictionary of metrics
        """
        if not self.round_history:
            return {}
        
        return {
            'total_rounds': len(self.round_history),
            'avg_clients_per_round': sum(r['clients_selected'] for r in self.round_history) / len(self.round_history),
            'avg_updates_received': sum(r['updates_received'] for r in self.round_history) / len(self.round_history),
            'round_history': self.round_history
        }

