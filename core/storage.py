#!/usr/bin/env python3
"""
core.storage
============

Laden, Validieren und Speichern der config.json.
CRUD-Helpers für Buttons.  *Keine* ID-Eindeutigkeits-Pflicht,
damit der Anwender Buttons mit gleichem Namen (ID) anlegen darf.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from jsonschema import validate, ValidationError

from util.paths import to_relative


# -------------------------------------------------------------------
# JSON-Schema  →  Beschreibung siehe Konzeptdokument
# -------------------------------------------------------------------
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
                "id":          {"type": "string"},
                "label":       {"type": "string"},      # = id (Altlast)
                "action": {
                    "type": "string",
                    "enum": ["SCRIPT", "LINK", "FILE", "FOLDER", "MENU"]
                },
                "payload":     {"type": "string"},
                "icon":        {"type": "string"},
                "parent":      {"type": ["string", "null"]},
                "description": {"type": "string"},
                "position": {
                    "type": "object",
                    "properties": {
                        "row": {"type": "integer"},
                        "col": {"type": "integer"}
                    },
                    "required": ["row", "col"],
                    "additionalProperties": False
                }
            },
            "required": ["id", "action", "icon", "parent"],
            "additionalProperties": False
        }
    }
}


class StorageError(Exception):
    """Basis-Exception für alle Storage-Operationen."""


# -------------------------------------------------------------------
# Laden & Speichern
# -------------------------------------------------------------------
def load_config(cfg_path: Path) -> dict:
    """Liest und validiert die Konfigurationsdatei."""
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        validate(data, SCHEMA)
        return data
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise StorageError(f"Config error: {exc}")


def save_config(cfg_path: Path, config: dict) -> None:
    """Schreibt die geänderte Config zurück auf die Platte (schön formatiert)."""
    try:
        # relative Pfade erzwingen, um Portabilität zu wahren
        for b in config["buttons"]:
            if b.get("payload"):
                b["payload"] = to_relative(b["payload"])
            b["icon"] = to_relative(b["icon"])
        validate(config, SCHEMA)            # letzte Sicherung
        cfg_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    except (OSError, ValidationError) as exc:
        raise StorageError(f"Save error: {exc}")


# -------------------------------------------------------------------
# CRUD-Helpers
# -------------------------------------------------------------------
def _idx(buttons: List[dict], btn_id: str) -> int | None:
    """Gibt den ERSTEN Index einer ID zurück (IDs dürfen doppelt sein)."""
    for i, b in enumerate(buttons):
        if b["id"] == btn_id:
            return i
    return None


def add_button(config: dict, btn: dict) -> None:
    """Fügt einen neuen Button an."""
    config["buttons"].append(btn)


def update_button(config: dict, btn: dict) -> None:
    """Ersetzt den ersten gefundenen Button mit gleicher ID."""
    i = _idx(config["buttons"], btn["id"])
    if i is None:
        raise StorageError(f"Button-ID '{btn['id']}' nicht gefunden.")
    config["buttons"][i] = btn


def delete_button_recursive(config: dict, btn_id: str) -> None:
    """Löscht Button UND alle Nachkommen (rekursiv)."""
    to_delete = {btn_id}
    changed = True
    while changed:
        changed = False
        for b in config["buttons"]:
            if b["parent"] in to_delete and b["id"] not in to_delete:
                to_delete.add(b["id"])
                changed = True
    config["buttons"] = [b for b in config["buttons"] if b["id"] not in to_delete]
