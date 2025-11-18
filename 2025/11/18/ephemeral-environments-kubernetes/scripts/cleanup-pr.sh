#!/bin/bash
set -e

PR_NUMBER=$1

if [ -z "$PR_NUMBER" ]; then
  echo "Usage: ./cleanup-pr.sh <PR_NUMBER>"
  exit 1
fi

NAMESPACE="pr-$PR_NUMBER"

echo "Cleaning up PR environment: $NAMESPACE"

# Delete namespace (this deletes all resources)
kubectl delete namespace $NAMESPACE --ignore-not-found=true

# Optionally delete images
# docker rmi myapp:pr-$PR_NUMBER || true

echo "Cleanup complete for PR $PR_NUMBER"

