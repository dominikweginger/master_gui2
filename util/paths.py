#!/usr/bin/env python3
"""
util.paths
==========

Hilfsfunktionen zum Umgang mit relativen/absoluten Pfaden.
Alle persistierten Pfade in der config.json werden RELATIV
zum Projekt-Root gespeichert, um portable Set-ups zu erlauben.
"""
from __future__ import annotations

from pathlib import Path


# Projekt-Root = zwei Ebenen über dieser Datei (…/util/paths.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def project_root() -> Path:
    """Liefert den Projekt-Root als Path‐Objekt."""
    return _PROJECT_ROOT


def to_relative(path: str | Path) -> str:
    """
    Wandelt einen absoluten Pfad – falls innerhalb des Projekts –
    in einen relativen um. Externe Pfade bleiben unverändert.
    """
    p = Path(path).expanduser().resolve()
    try:
        return str(p.relative_to(_PROJECT_ROOT))
    except ValueError:
        return str(p)        # liegt außerhalb → nicht änderbar


def to_absolute(path: str | Path) -> Path:
    """
    Gibt IMMER einen absoluten Pfad zurück.
    Bereits absolute Pfade werden unverändert durchgereicht.
    """
    p = Path(path)
    return p if p.is_absolute() else _PROJECT_ROOT / p
