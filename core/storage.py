from pathlib import Path
import json
from jsonschema import validate, ValidationError

SCHEMA = {
    "type": "object",
    "properties": {
        "buttons": {
            "type": "array",
            "items": {"$ref": "#/definitions/button"}
        },
        "theme": {
            "type": "object",
            "properties": {
                "stylesheet": {"type": "string"},
                "background": {"type": "string"}
            },
            "required": ["stylesheet", "background"],
            "additionalProperties": False
        }
    },
    "required": ["buttons", "theme"],
    "additionalProperties": False,
    "definitions": {
        "button": {
            "type": "object",
            "properties": {
                "id":      {"type": "string"},
                "label":   {"type": "string"},
                "action":  {
                    "type": "string",
                    "enum": ["SCRIPT", "LINK", "GROUP", "FILE", "EXPLORER"]
                },
                "payload": {"type": "string"},
                "icon":    {"type": "string"},
                "size": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "integer"},
                        {"type": "integer"}
                    ],
                    "minItems": 2,
                    "maxItems": 2
                },
                "position": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "integer"},
                        {"type": "integer"}
                    ],
                    "minItems": 2,
                    "maxItems": 2
                },
                "page":    {"type": "integer"}
            },
            "required": ["id", "label", "action", "payload", "icon"],
            "additionalProperties": False
        }
    }
}

class StorageError(Exception):
    """Base exception for storage operations."""


def load_config(config_path: Path) -> dict:
    """
    Load and validate a JSON configuration file against the SCHEMA.
    :param config_path: Path to config.json
    :return: configuration data as dict
    :raises StorageError: on file read or schema validation errors
    """
    try:
        raw = config_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        raise StorageError(f"Error reading {config_path}: {e}")

    try:
        validate(instance=data, schema=SCHEMA)
    except ValidationError as ve:
        raise StorageError(f"JSON schema validation failed: {ve.message}")

    return data


def save_config(config_path: Path, data: dict) -> None:
    """
    Validate and save configuration data to JSON file.
    :param config_path: Path to config.json
    :param data: dict of configuration data
    :raises StorageError: on validation or write errors
    """
    try:
        validate(instance=data, schema=SCHEMA)
    except ValidationError as ve:
        raise StorageError(f"JSON schema validation failed: {ve.message}")

    try:
        config_path.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception as e:
        raise StorageError(f"Error writing {config_path}: {e}")
