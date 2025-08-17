#!/usr/bin/env python3
"""
util.paths
==========

Hilfsfunktionen zum Umgang mit relativen/absoluten Pfaden.
Alle persistierten Pfade in der config.json werden RELATIV
zum Projekt-Root gespeichert, um portable Set-ups zu erlauben.

NEU (Patch A):
- Im PyInstaller-EXE-Modus (sys.frozen) liegt der sinnvolle Projekt-Root
  beim Ordner der EXE (Path(sys.executable).parent) – nicht im Temp-Entpackpfad.
"""
from __future__ import annotations

import sys
from pathlib import Path

def _detect_project_root() -> Path:
    # Im Dev-Modus: zwei Ebenen über dieser Datei (…/util/paths.py)
    dev_root = Path(__file__).resolve().parent.parent
    # Im EXE-Modus (PyInstaller): Ordner der EXE-Datei
    if getattr(sys, "frozen", False):  # PyInstaller
        return Path(sys.executable).resolve().parent
    return dev_root

# Projekt-Root (dev oder EXE)
_PROJECT_ROOT: Path = _detect_project_root()

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
    return p if p.is_absolute() else (_PROJECT_ROOT / p).resolve()
