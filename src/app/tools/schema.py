"""Minimal schema-validation helpers for tool payloads."""

from app.tools.exceptions import ToolValidationError


def validate_payload(schema: dict, payload: dict, *, label: str) -> None:
    """Validate a dict payload against the supported subset of JSON schema."""
    if not schema:
        return
    schema_type = schema.get("type")
    if schema_type and schema_type != "object":
        raise ToolValidationError(f"{label} schema root must be an object.")
    if not isinstance(payload, dict):
        raise ToolValidationError(f"{label} payload must be an object.")

    required = schema.get("required", [])
    for field_name in required:
        if field_name not in payload:
            raise ToolValidationError(f"Missing required field '{field_name}' in {label} payload.")

    properties = schema.get("properties", {})
    for key, value in payload.items():
        if key not in properties:
            continue
        expected_type = properties[key].get("type")
        if expected_type and not _matches_type(expected_type, value):
            raise ToolValidationError(
                f"Field '{key}' in {label} payload must be of type {expected_type}."
            )


def _matches_type(expected_type: str, value: object) -> bool:
    """Map JSON-schema scalar names to simple Python type predicates."""
    type_map = {
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "array": lambda item: isinstance(item, list),
        "object": lambda item: isinstance(item, dict),
    }
    predicate = type_map.get(expected_type)
    if predicate is None:
        return True
    return predicate(value)
