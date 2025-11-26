"""Example: Federated Learning with Differential Privacy

Shows how to add differential privacy noise to updates.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import copy

from src.coordinator import FLCoordinator
from src.client import FLClient
from src.differential_privacy import add_dp_noise, PrivacyBudget


def create_simple_model(input_size=784, hidden_size=128, num_classes=10):
    """Create a simple MLP model"""
    return nn.Sequential(
        nn.Linear(input_size, hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, num_classes)
    )


def generate_non_iid_data(client_id, num_clients, samples_per_client=100):
    """Generate non-IID data for a client"""
    input_size = 784
    num_classes = 10
    
    classes_per_client = 2
    start_class = (client_id * classes_per_client) % num_classes
    classes = list(range(start_class, start_class + classes_per_client))
    classes = [c % num_classes for c in classes]
    
    X = []
    y = []
    
    for _ in range(samples_per_client):
        features = torch.randn(input_size)
        label = torch.tensor(classes[torch.randint(0, len(classes), (1,)).item()])
        X.append(features)
        y.append(label)
    
    X = torch.stack(X)
    y = torch.stack(y)
    
    return DataLoader(TensorDataset(X, y), batch_size=32, shuffle=True)


def main():
    """Run federated learning with differential privacy"""
    print("=" * 60)
    print("Federated Learning with Differential Privacy")
    print("=" * 60)
    
    # Configuration
    num_clients = 10
    clients_per_round = 5
    local_epochs = 3
    learning_rate = 0.01
    dp_epsilon = 1.0
    dp_delta = 1e-5
    
    # Create coordinator with DP enabled
    coordinator = FLCoordinator(
        num_clients=num_clients,
        clients_per_round=clients_per_round,
        local_epochs=local_epochs,
        learning_rate=learning_rate,
        use_quantization=True,
        quantization_bits=8,
        use_dp=True,
        dp_epsilon=dp_epsilon,
        dp_delta=dp_delta
    )
    
    # Create global model
    global_model = create_simple_model()
    print(f"\nGlobal model created: {sum(p.numel() for p in global_model.parameters())} parameters")
    print(f"Differential Privacy: epsilon={dp_epsilon}, delta={dp_delta}")
    
    # Create clients
    clients = []
    privacy_budgets = {}
    
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
        
        # Initialize privacy budget for each client
        privacy_budgets[i] = PrivacyBudget(total_epsilon=10.0)
    
    # Run federated round
    print("\n" + "=" * 60)
    print("Running Federated Learning Round with DP")
    print("=" * 60)
    
    # Select clients
    selected_clients = coordinator.select_clients(clients)
    print(f"Selected {len(selected_clients)} clients")
    
    # Check privacy budgets
    round_epsilon = 1.0
    participating_clients = []
    for client in selected_clients:
        if privacy_budgets[client.client_id].can_participate(round_epsilon):
            participating_clients.append(client)
            privacy_budgets[client.client_id].use(round_epsilon)
        else:
            print(f"Client {client.client_id} cannot participate (privacy budget exhausted)")
    
    if not participating_clients:
        print("No clients can participate due to privacy budget constraints")
        return
    
    # Send global model
    coordinator.send_global_model(global_model, participating_clients)
    
    # Collect updates and add DP noise
    updates = []
    for client in participating_clients:
        update = client.send_update()
        if update is not None:
            # Add differential privacy noise
            if coordinator.use_dp:
                update['weights'] = add_dp_noise(
                    update['weights'],
                    epsilon=coordinator.dp_epsilon,
                    delta=coordinator.dp_delta,
                    sensitivity=1.0,
                    clip_norm=1.0
                )
            updates.append(update)
    
    print(f"Collected {len(updates)} updates (with DP noise)")
    
    # Aggregate
    if updates:
        aggregated_weights = coordinator.aggregator.aggregate(updates)
        global_model.load_state_dict(aggregated_weights)
        print("Global model updated with DP-protected updates")
    
    # Print privacy budget status
    print("\n" + "=" * 60)
    print("Privacy Budget Status")
    print("=" * 60)
    for client_id, budget in privacy_budgets.items():
        if client_id in [c.client_id for c in participating_clients]:
            print(f"Client {client_id}: {budget.used_epsilon:.2f}/{budget.total_epsilon:.2f} epsilon used")
    
    print("\nRound completed with differential privacy protection!")


if __name__ == "__main__":
    main()

