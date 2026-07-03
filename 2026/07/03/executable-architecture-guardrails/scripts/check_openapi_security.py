#!/usr/bin/env python3
"""check_openapi_security.py - Validate OpenAPI security schemes exist."""
import sys
import yaml


def main():
    if len(sys.argv) < 2:
        print("FAIL: Missing OpenAPI file path. Usage: python check_openapi_security.py <openapi.yaml>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r") as f:
        spec = yaml.safe_load(f)

    if not spec:
        print("FAIL: OpenAPI spec is empty")
        sys.exit(1)

    components = spec.get("components")
    if not components or "securitySchemes" not in components:
        print(f"FAIL: {path} is missing components.securitySchemes. Every public API must define auth.")
        sys.exit(1)

    count = len(components["securitySchemes"])
    print(f"PASS: {path} has {count} security scheme(s) defined")
    sys.exit(0)


if __name__ == "__main__":
    main()
