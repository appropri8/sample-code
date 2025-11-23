/**
 * Model signature verification for MCU devices (C++)
 * 
 * This is a reference implementation showing how to verify model signatures
 * using mbedTLS on constrained devices.
 */

#include <mbedtls/pk.h>
#include <mbedtls/sha256.h>
#include <mbedtls/base64.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>

// Public key (should be stored in secure element or embedded in firmware)
#define PUBLIC_KEY_PEM \
"-----BEGIN PUBLIC KEY-----\n" \
"MFkwEwYHKoZIzj0CAQYIKoZIzj0CAQcDQgAE...\n" \
"-----END PUBLIC KEY-----\n"

typedef struct {
    uint8_t* model_data;
    size_t model_size;
    uint8_t* signature;
    size_t signature_size;
    char* model_id;
    char* model_version;
} model_package_t;

/**
 * Verify model signature
 * Returns 0 on success, non-zero on failure
 */
int verify_model_signature(model_package_t* package) {
    mbedtls_pk_context pk;
    mbedtls_sha256_context sha256;
    unsigned char hash[32];
    int ret;

    // Initialize
    mbedtls_pk_init(&pk);
    mbedtls_sha256_init(&sha256);

    // Parse public key
    ret = mbedtls_pk_parse_public_key(&pk, 
        (const unsigned char*)PUBLIC_KEY_PEM, 
        strlen(PUBLIC_KEY_PEM) + 1);
    if (ret != 0) {
        printf("Failed to parse public key: %d\n", ret);
        goto cleanup;
    }

    // Hash model data
    ret = mbedtls_sha256_starts_ret(&sha256, 0);
    if (ret != 0) goto cleanup;
    
    ret = mbedtls_sha256_update_ret(&sha256, 
        package->model_data, 
        package->model_size);
    if (ret != 0) goto cleanup;
    
    ret = mbedtls_sha256_finish_ret(&sha256, hash);
    if (ret != 0) goto cleanup;

    // Verify signature
    ret = mbedtls_pk_verify(&pk, MBEDTLS_MD_SHA256,
        hash, 32,
        package->signature, package->signature_size);
    
    if (ret == 0) {
        printf("Model signature verified: %s v%s\n", 
            package->model_id, package->model_version);
    } else {
        printf("Model signature verification failed: %d\n", ret);
    }

cleanup:
    mbedtls_pk_free(&pk);
    mbedtls_sha256_free(&sha256);
    return ret;
}

/**
 * Load model safely (verify before loading)
 * Returns 0 on success, non-zero on failure
 */
int load_model_safely(model_package_t* package) {
    // Verify signature first
    int ret = verify_model_signature(package);
    if (ret != 0) {
        return -1; // Refuse to load
    }

    // Additional checks could go here:
    // - Verify checksum
    // - Check model version
    // - Check device group

    // Load model
    // ... model loading code ...

    return 0;
}

// Example usage (commented out - requires actual model data)
/*
int main() {
    model_package_t package = {
        .model_data = (uint8_t*)model_bytes,
        .model_size = model_size,
        .signature = (uint8_t*)signature_bytes,
        .signature_size = signature_size,
        .model_id = "object_detector_v2",
        .model_version = "2.1.1"
    };
    
    if (load_model_safely(&package) == 0) {
        printf("Model loaded successfully\n");
    } else {
        printf("Failed to load model\n");
    }
    
    return 0;
}
*/

