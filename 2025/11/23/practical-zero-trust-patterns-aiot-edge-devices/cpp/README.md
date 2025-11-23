# C++ Model Verification (MCU)

This directory contains C++ implementation of model signature verification for microcontroller units (MCUs).

## Requirements

- mbedTLS library
- C++11 or later
- CMake (optional, for build system)

## Building

### With CMake

```bash
mkdir build
cd build
cmake ..
make
```

### Manual Build

```bash
g++ -std=c++11 model_verification.cpp -lmbedtls -lmbedx509 -lmbedcrypto -o model_verifier
```

## Usage

See `model_verification.cpp` for the implementation. This is a reference implementation showing how to verify model signatures using mbedTLS on constrained devices.

## Notes

- Public key should be embedded in firmware or stored in secure element
- Signature verification uses ECDSA with SHA-256
- Model hash is computed using SHA-256
- Error handling is simplified for demonstration

