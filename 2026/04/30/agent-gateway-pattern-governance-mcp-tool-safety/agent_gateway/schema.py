class ValidationError(ValueError):
    pass


def validate_json(schema, value, path="$"):
    expected = schema.get("type")

    if expected == "object":
        if not isinstance(value, dict):
            raise ValidationError(f"{path} must be an object")

        required = schema.get("required", [])
        for field in required:
            if field not in value:
                raise ValidationError(f"{path}.{field} is required")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                names = ", ".join(sorted(extra))
                raise ValidationError(f"{path} has unknown field(s): {names}")

        for field, field_value in value.items():
            if field in properties:
                validate_json(properties[field], field_value, f"{path}.{field}")
        return

    if expected == "array":
        if not isinstance(value, list):
            raise ValidationError(f"{path} must be an array")
        return

    if expected == "string":
        if not isinstance(value, str):
            raise ValidationError(f"{path} must be a string")
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        if min_length is not None and len(value) < min_length:
            raise ValidationError(f"{path} must be at least {min_length} characters")
        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"{path} must be at most {max_length} characters")
        if "enum" in schema and value not in schema["enum"]:
            raise ValidationError(f"{path} must be one of {schema['enum']}")
        return

    if expected == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"{path} must be a number")
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            raise ValidationError(f"{path} must be >= {minimum}")
        if maximum is not None and value > maximum:
            raise ValidationError(f"{path} must be <= {maximum}")
        return

    if expected == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError(f"{path} must be an integer")
        return

    if expected == "boolean":
        if not isinstance(value, bool):
            raise ValidationError(f"{path} must be a boolean")
        return

