"""Example: Complete Federated Learning Round

Simulates a federated learning round with multiple clients.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import copy

from src.coordinator import FLCoordinator
from src.client import FLClient


def create_simple_model(input_size=784, hidden_size=128, num_classes=10):
    """Create a simple MLP model"""
    return nn.Sequential(
        nn.Linear(input_size, hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, num_classes)
    )


def generate_non_iid_data(client_id, num_clients, samples_per_client=100):
    """Generate non-IID data for a client
    
    Each client gets data from a subset of classes.
    """
    # Create synthetic data
    input_size = 784
    num_classes = 10
    
    # Each client gets data from 2-3 classes
    classes_per_client = 2
    start_class = (client_id * classes_per_client) % num_classes
    classes = list(range(start_class, start_class + classes_per_client))
    classes = [c % num_classes for c in classes]
    
    # Generate data
    X = []
    y = []
    
    for _ in range(samples_per_client):
        # Random feature vector
        features = torch.randn(input_size)
        # Label from client's classes
        label = torch.tensor(classes[torch.randint(0, len(classes), (1,)).item()])
        X.append(features)
        y.append(label)
    
    X = torch.stack(X)
    y = torch.stack(y)
    
    return DataLoader(TensorDataset(X, y), batch_size=32, shuffle=True)


def main():
    """Run federated learning simulation"""
    print("=" * 60)
    print("Federated Learning Round Simulation")
    print("=" * 60)
    
    # Configuration
    num_clients = 10
    clients_per_round = 5
    local_epochs = 3
    learning_rate = 0.01
    
    # Create coordinator
    coordinator = FLCoordinator(
        num_clients=num_clients,
        clients_per_round=clients_per_round,
        local_epochs=local_epochs,
        learning_rate=learning_rate,
        use_quantization=True,
        quantization_bits=8
    )
    
    # Create global model
    global_model = create_simple_model()
    print(f"\nGlobal model created: {sum(p.numel() for p in global_model.parameters())} parameters")
    
    # Create clients with non-IID data
    clients = []
    for i in range(num_clients):
        local_data = generate_non_iid_data(i, num_clients, samples_per_client=100)
        client = FLClient(
            client_id=i,
            local_data=local_data,
            model=copy.deepcopy(global_model),
            learning_rate=learning_rate,
            use_quantization=True,
            quantization_bits=8
        )
        clients.append(client)
        print(f"Client {i}: {len(local_data.dataset)} samples")
    
    # Run federated round
    print("\n" + "=" * 60)
    print("Running Federated Learning Round")
    print("=" * 60)
    
    new_global_model = coordinator.run_round(global_model, clients)
    
    # Print metrics
    print("\n" + "=" * 60)
    print("Round Metrics")
    print("=" * 60)
    metrics = coordinator.get_metrics()
    for key, value in metrics.items():
        if key != 'round_history':
            print(f"{key}: {value}")
    
    print("\nRound completed successfully!")
    print(f"Model updated with aggregated weights from {metrics.get('avg_updates_received', 0):.1f} clients on average")


if __name__ == "__main__":
    main()

