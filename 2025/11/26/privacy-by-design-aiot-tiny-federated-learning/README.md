# Privacy-by-Design AIoT: Tiny Federated Learning

A complete implementation of federated learning for AIoT devices with privacy protection, quantization, and efficient communication.

## Features

- **Federated Coordinator**: Manages FL rounds, device selection, and aggregation
- **Client Simulation**: Simulates multiple devices with different local datasets
- **Weight Quantization**: 8-bit and 4-bit quantization to reduce update size
- **Differential Privacy**: Optional noise addition for privacy protection
- **FedAvg Aggregation**: Standard federated averaging algorithm
- **Device-Side Pseudocode**: Examples for MicroPython/C++ implementation
- **Configuration**: YAML/JSON configs for FL parameters

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Run Federated Learning Simulation

```bash
python examples/federated_round_example.py
```

This simulates a complete federated learning round with:
- 10 clients (devices)
- Simple MLP model for classification
- Non-IID data distribution
- FedAvg aggregation
- Metrics per client group

### Run with Differential Privacy

```bash
python examples/dp_federated_example.py
```

This adds differential privacy noise to updates before aggregation.

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── coordinator.py          # FL coordinator with round management
│   ├── client.py               # FL client simulation
│   ├── aggregator.py           # FedAvg and other aggregation methods
│   ├── quantization.py        # Weight quantization utilities
│   └── differential_privacy.py # DP noise addition
├── examples/
│   ├── federated_round_example.py
│   ├── dp_federated_example.py
│   └── device_pseudocode.py    # Device-side implementation examples
├── configs/
│   ├── fl_config.yaml          # FL round parameters
│   └── privacy_config.json     # Privacy settings
├── tests/
│   ├── test_coordinator.py
│   ├── test_aggregator.py
│   └── test_quantization.py
├── requirements.txt
└── README.md
```

## Usage Examples

### Basic Federated Learning Round

```python
from src.coordinator import FLCoordinator
from src.client import FLClient
import torch
import torch.nn as nn

# Create coordinator
coordinator = FLCoordinator(
    num_clients=10,
    local_epochs=3,
    learning_rate=0.01
)

# Create global model
global_model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
)

# Create clients with local data
clients = []
for i in range(10):
    client = FLClient(
        client_id=i,
        local_data=generate_local_data(i),  # Non-IID data
        model=copy.deepcopy(global_model)
    )
    clients.append(client)

# Run federated round
new_global_model = coordinator.run_round(global_model, clients)
```

### With Quantization

```python
from src.quantization import quantize_weights, dequantize_weights

# Quantize updates before sending
quantized_update, scale, zero_point = quantize_weights(update, bits=8)

# Dequantize on coordinator
update = dequantize_weights(quantized_update, scale, zero_point)
```

### With Differential Privacy

```python
from src.differential_privacy import add_dp_noise

# Add noise to update
noisy_update = add_dp_noise(
    update,
    epsilon=1.0,
    delta=1e-5,
    sensitivity=1.0
)
```

## Configuration

### FL Round Parameters (configs/fl_config.yaml)

```yaml
federated_learning:
  num_clients: 10
  clients_per_round: 5
  local_epochs: 3
  learning_rate: 0.01
  batch_size: 32
  
communication:
  max_payload_size_kb: 10
  quantization_bits: 8
  use_sparse_updates: true
  sparse_threshold: 0.01
  
round_schedule:
  frequency: "daily"
  time: "02:00 UTC"
  min_participants: 5
  max_participants: 20
```

### Privacy Settings (configs/privacy_config.json)

```json
{
  "differential_privacy": {
    "enabled": true,
    "epsilon": 1.0,
    "delta": 1e-5,
    "sensitivity": 1.0,
    "clip_gradients": true,
    "max_gradient_norm": 1.0
  },
  "secure_aggregation": {
    "enabled": false,
    "method": "dummy_noise"
  },
  "device_attestation": {
    "enabled": true,
    "require_signature": true
  }
}
```

## Device-Side Implementation

See `examples/device_pseudocode.py` for MicroPython/C++-like pseudocode showing:
- Loading initial model weights
- Collecting local dataset
- Running training steps
- Serializing and sending updates
- Receiving updated global weights

## Testing

```bash
pytest tests/
```

## License

MIT

