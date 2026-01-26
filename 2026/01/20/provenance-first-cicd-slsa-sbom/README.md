# Provenance-First CI/CD: SLSA Attestations + SBOM Checks

A complete example showing how to add provenance attestations, signing, and SBOM policy gates to a GitHub Actions pipeline.

## Overview

This repository demonstrates:

- **Complete GitHub Actions workflow**: Build, SBOM generation, vulnerability scanning, signing, and provenance attestation
- **Policy gate script**: Bash script that fails builds on CVE thresholds
- **SBOM verification**: Verifies SBOM at deploy time against license and registry policies
- **Waiver management**: Scripts for handling exceptions with time-boxed waivers
- **Metrics collection**: Scripts for tracking provenance and policy gate metrics

## Features

- ✅ Automatic SBOM generation using `syft`
- ✅ Vulnerability scanning using `grype`
- ✅ Container image signing using `cosign` (keyless with GitHub Actions OIDC)
- ✅ SLSA-compliant provenance attestations
- ✅ Policy gates that block releases on CVE thresholds
- ✅ Deploy-time verification of signatures and attestations
- ✅ Waiver management for exceptions
- ✅ Metrics tracking

## Prerequisites

- GitHub Actions enabled on your repository
- Docker installed (for building container images)
- GitHub Container Registry (ghcr.io) access

## Quick Start

### 1. Set Up Workflow

The main workflow is in `.github/workflows/build-and-verify.yml`. It will:
1. Build your container image
2. Generate SBOM
3. Scan for vulnerabilities
4. Sign the image
5. Generate provenance attestation
6. Attach SBOM as attestation
7. Run policy gate checks

### 2. Configure Policy Thresholds

Edit `scripts/policy-gate.sh` or set environment variables:

```bash
export MAX_CRITICAL=0
export MAX_HIGH=5
export MAX_MEDIUM=20
```

### 3. Run the Pipeline

Push to `main` branch or create a pull request. The workflow will run automatically.

## Workflow Details

### Build Stage

1. **Build Container Image**: Uses Docker Buildx to build and push to GitHub Container Registry
2. **Generate SBOM**: Uses `syft` to generate SPDX and CycloneDX SBOMs
3. **Scan Vulnerabilities**: Uses `grype` to scan the SBOM for known vulnerabilities

### Verify Stage

4. **Sign Image**: Uses `cosign` with keyless signing (GitHub Actions OIDC)
5. **Generate Provenance**: Uses GitHub Actions' built-in provenance attestation
6. **Attach SBOM**: Attaches SBOM as a cosign attestation
7. **Policy Gate**: Verifies CVE thresholds and blocks release if exceeded

### Deploy Stage

The deploy workflow (`.github/workflows/deploy.yml`) verifies:
- Image signature
- SBOM attestation
- SBOM policy (licenses, registries)

## Scripts

### Policy Gate (`scripts/policy-gate.sh`)

Fails the build if CVE thresholds are exceeded:

```bash
./scripts/policy-gate.sh vulnerabilities.json
```

**Thresholds:**
- Critical: 0 (default)
- High: 5 (default)
- Medium: 20 (default)

**Override via environment variables:**
```bash
export MAX_CRITICAL=0
export MAX_HIGH=5
export MAX_MEDIUM=20
```

### SBOM Verification (`scripts/verify-sbom-policy.sh`)

Verifies SBOM against license and registry policies:

```bash
./scripts/verify-sbom-policy.sh sbom.json
```

**Checks:**
- Approved licenses (MIT, Apache-2.0, BSD-3-Clause, etc.)
- Approved registries (npmjs.org, pypi.org, maven.org, etc.)

**Configure via environment variables:**
```bash
export APPROVED_LICENSES="MIT,Apache-2.0,BSD-3-Clause"
export APPROVED_REGISTRIES="npmjs.org,pypi.org,docker.io"
```

### Waiver Request (`scripts/waiver-request.sh`)

Creates a waiver request for a CVE or policy violation:

```bash
./scripts/waiver-request.sh CVE-2024-1234 "False positive, not exploitable" 30
```

This creates a JSON file in `waivers/` that requires approval.

### Metrics (`scripts/metrics.sh`)

Collects metrics about provenance and policy gates:

```bash
./scripts/metrics.sh
```

**Metrics tracked:**
- % releases with verified provenance
- Policy gate failure rate
- Active/expired waivers

## Deploy-Time Verification

The deploy workflow verifies signatures and attestations before deploying:

```bash
# Verify signature
cosign verify \
  --certificate-identity-regexp "https://github.com/your-org/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/your-org/your-image:tag

# Verify SBOM attestation
cosign verify-attestation \
  --type spdx \
  --certificate-identity-regexp "https://github.com/your-org/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/your-org/your-image:tag
```

## Policy Gate Examples

### Example 1: Block on Critical CVEs

```bash
# Set threshold
export MAX_CRITICAL=0

# Run policy gate
./scripts/policy-gate.sh vulnerabilities.json
```

If any critical CVEs are found, the build fails.

### Example 2: Allow Some High CVEs

```bash
# Set threshold
export MAX_HIGH=5

# Run policy gate
./scripts/policy-gate.sh vulnerabilities.json
```

Build fails only if more than 5 high-severity CVEs are found.

### Example 3: Request Waiver

```bash
# Create waiver request
./scripts/waiver-request.sh CVE-2024-1234 \
  "False positive: not exploitable in containerized environment" \
  30

# Submit for approval (manual step)
# Once approved, update waivers/CVE-2024-1234.json
```

## Artifacts Generated

The pipeline generates:

1. **Container Image**: Signed and pushed to GitHub Container Registry
2. **SBOM**: SPDX and CycloneDX formats
3. **Provenance Attestation**: SLSA-compliant provenance
4. **Vulnerability Report**: JSON file with all detected vulnerabilities
5. **Signatures**: Cryptographic signatures for image and attestations

## Verification Commands

### Verify Image Signature

```bash
cosign verify \
  --certificate-identity-regexp "https://github.com/your-org/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/your-org/your-image:tag
```

### Verify SBOM Attestation

```bash
cosign verify-attestation \
  --type spdx \
  --certificate-identity-regexp "https://github.com/your-org/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/your-org/your-image:tag
```

### Download SBOM

```bash
cosign download attestation --type spdx \
  ghcr.io/your-org/your-image:tag | \
  jq -r '.payload' | base64 -d | jq -r '.predicate' > sbom.json
```

## Operational Notes

### Key Management

This example uses **keyless signing** with GitHub Actions OIDC. No key management required.

For other CI systems, use managed keys:
- AWS KMS
- Google Cloud KMS
- Azure Key Vault
- HashiCorp Vault

### Handling Exceptions

Use waivers for time-boxed exceptions:

1. Create waiver request: `./scripts/waiver-request.sh CVE-2024-1234 "reason" 30`
2. Submit for approval (ticketing system)
3. Security team reviews and approves
4. Waiver expires after specified days

### Audit Trail

Policy decisions are logged to `policy-decisions.log`:

```
2026-01-20T10:30:00Z | ALLOW | abc123 | build-and-verify | 12345
2026-01-20T11:00:00Z | DENY | def456 | build-and-verify | 12346
```

## Metrics

Track these metrics:

- **% releases with verified provenance**: Target 100%
- **Mean time to patch critical dependency issues**: Target < 7 days
- **Policy gate failure rate**: Monitor trends

Run metrics collection:

```bash
./scripts/metrics.sh
```

## Troubleshooting

### Policy Gate Fails Unexpectedly

1. Check vulnerability file: `cat vulnerabilities.json | jq '.matches[] | select(.vulnerability.severity == "Critical")'`
2. Review thresholds: `echo $MAX_CRITICAL $MAX_HIGH $MAX_MEDIUM`
3. Check for false positives

### Signature Verification Fails

1. Verify certificate identity regex matches your repository
2. Check OIDC issuer matches GitHub Actions
3. Ensure image tag is correct

### SBOM Generation Fails

1. Ensure `syft` is installed
2. Check image is accessible
3. Verify image format is supported

## Next Steps

1. **Customize thresholds**: Adjust CVE thresholds for your risk tolerance
2. **Add license checks**: Enforce license policies in SBOM verification
3. **Set up metrics dashboard**: Track provenance and policy gate metrics
4. **Add regression gates**: Compare metrics to baseline in CI
5. **Integrate with deployment**: Add verification to your deployment pipeline

## References

- [SLSA Framework](https://slsa.dev/)
- [Cosign Documentation](https://docs.sigstore.dev/cosign/overview/)
- [Syft Documentation](https://github.com/anchore/syft)
- [Grype Documentation](https://github.com/anchore/grype)
- [GitHub Actions Attestations](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

## License

This code is provided as example code for educational purposes.
