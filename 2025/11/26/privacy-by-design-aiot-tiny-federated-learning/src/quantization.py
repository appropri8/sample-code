"""Weight Quantization Utilities

Quantize model weights to reduce communication size.
"""

import torch
import numpy as np
from typing import Tuple


def quantize_weights(
    weights: torch.Tensor,
    bits: int = 8
) -> Tuple[torch.Tensor, float, float]:
    """Quantize weights to reduce size
    
    Args:
        weights: Original float32 weights
        bits: Number of bits for quantization (8 or 4)
        
    Returns:
        Tuple of (quantized_weights, scale, zero_point)
    """
    weights_np = weights.detach().cpu().numpy()
    
    # Find min and max
    w_min = float(weights_np.min())
    w_max = float(weights_np.max())
    
    # Handle case where all weights are the same
    if w_max == w_min:
        return torch.zeros_like(weights, dtype=torch.uint8), 1.0, 0.0
    
    # Compute scale and zero point
    q_min = 0
    q_max = (2 ** bits) - 1
    
    scale = (w_max - w_min) / (q_max - q_min)
    zero_point = q_min - w_min / scale
    
    # Quantize
    quantized = np.round(weights_np / scale + zero_point).clip(q_min, q_max)
    quantized = torch.from_numpy(quantized).to(weights.device).to(torch.uint8)
    
    return quantized, scale, zero_point


def dequantize_weights(
    quantized: torch.Tensor,
    scale: float,
    zero_point: float
) -> torch.Tensor:
    """Dequantize weights back to float32
    
    Args:
        quantized: Quantized uint8 weights
        scale: Quantization scale
        zero_point: Quantization zero point
        
    Returns:
        Dequantized float32 weights
    """
    dequantized = (quantized.float() - zero_point) * scale
    return dequantized


def compute_compression_ratio(
    original_size: int,
    quantized_size: int
) -> float:
    """Compute compression ratio
    
    Args:
        original_size: Size of original weights in bytes
        quantized_size: Size of quantized weights in bytes
        
    Returns:
        Compression ratio (original_size / quantized_size)
    """
    if quantized_size == 0:
        return 0.0
    return original_size / quantized_size

