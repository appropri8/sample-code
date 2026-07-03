#!/bin/bash
# check-owner.sh - CI fitness function
# Usage: bash check-owner.sh <service-name>
# Ensures every service has an owner assigned in service.yaml.

set -euo pipefail

SERVICE_NAME="${1:-}"
SERVICE_FILE="services/${SERVICE_NAME}/service.yaml"

if [ -z "$SERVICE_NAME" ]; then
    echo "FAIL: Service name not provided. Usage: $0 <service-name>"
    exit 1
fi

if [ ! -f "$SERVICE_FILE" ]; then
    echo "FAIL: ${SERVICE_FILE} is missing. Create service metadata using the golden path template."
    exit 1
fi

OWNER=$(python3 -c "import yaml; print(yaml.safe_load(open('${SERVICE_FILE}'))['service']['owner'])")
if [ -z "$OWNER" ] || [ "$OWNER" == "null" ]; then
    echo "FAIL: ${SERVICE_NAME} has no owner assigned in service.yaml"
    exit 1
fi

echo "PASS: ${SERVICE_NAME} owned by ${OWNER}"
