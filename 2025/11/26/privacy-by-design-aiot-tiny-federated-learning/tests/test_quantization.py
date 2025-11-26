"""Tests for weight quantization"""

import torch
import pytest
from src.quantization import quantize_weights, dequantize_weights, compute_compression_ratio


def test_quantize_dequantize_8bit():
    """Test 8-bit quantization and dequantization"""
    # Create test weights
    weights = torch.randn(100, 50) * 2.0  # Range roughly [-4, 4]
    
    # Quantize
    quantized, scale, zero_point = quantize_weights(weights, bits=8)
    
    # Check quantization
    assert quantized.dtype == torch.uint8
    assert quantized.min() >= 0
    assert quantized.max() <= 255
    
    # Dequantize
    dequantized = dequantize_weights(quantized, scale, zero_point)
    
    # Check reconstruction error (should be small)
    error = torch.abs(weights - dequantized)
    max_error = error.max().item()
    assert max_error < 0.1  # Should be small for 8-bit


def test_quantize_dequantize_4bit():
    """Test 4-bit quantization and dequantization"""
    weights = torch.randn(100, 50) * 2.0
    
    quantized, scale, zero_point = quantize_weights(weights, bits=4)
    
    assert quantized.dtype == torch.uint8
    assert quantized.min() >= 0
    assert quantized.max() <= 15
    
    dequantized = dequantize_weights(quantized, scale, zero_point)
    
    # 4-bit should have larger error
    error = torch.abs(weights - dequantized)
    max_error = error.max().item()
    assert max_error < 0.5  # Larger tolerance for 4-bit


def test_compression_ratio():
    """Test compression ratio calculation"""
    original_size = 1000 * 4  # 1000 floats * 4 bytes
    quantized_size = 1000 * 1  # 1000 uint8 * 1 byte
    
    ratio = compute_compression_ratio(original_size, quantized_size)
    assert ratio == 4.0  # 4x compression


def test_quantize_constant_weights():
    """Test quantization of constant weights"""
    weights = torch.ones(10, 10) * 5.0  # All same value
    
    quantized, scale, zero_point = quantize_weights(weights, bits=8)
    dequantized = dequantize_weights(quantized, scale, zero_point)
    
    # Should handle constant weights gracefully
    assert torch.allclose(weights, dequantized, atol=0.1)

