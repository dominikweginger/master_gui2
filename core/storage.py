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
                    "enum": ["SCRIPT", "LINK", "FILE", "EXPLORER", "MENU"]
                },
                "payload": {"type": "string"},
                "icon":    {"type": "string"},
                "parent":  {"type": ["string", "null"]},
                "size": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {"type": "integer"}
                }
            },
            "required": ["id", "label", "action", "icon", "parent"],
            "additionalProperties": False
        }
    }
}


class StorageError(Exception):
    """Base exception for storage operations."""


def load_config(config_path: Path) -> dict:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        validate(instance=data, schema=SCHEMA)
        return data
    except (OSError, json.JSONDecodeError, ValidationError) as e:
        raise StorageError(f"Config error: {e}")
