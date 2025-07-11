#!/usr/bin/env python3
"""
core.models
===========

Einfaches Domain-Model für Buttons, damit wir Typhints
nutzen können, ohne PySide-Klassen durchs Projekt zu reichen.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class ButtonAction(Enum):
    SCRIPT   = "SCRIPT"
    LINK     = "LINK"
    FILE     = "FILE"          # inkl. .exe-Dateien
    FOLDER   = "FOLDER"
    MENU     = "MENU"          # Container für Children


@dataclass
class ButtonModel:
    id:          str
    action:      ButtonAction
    payload:     str | None
    icon:        str
    parent:      str | None
    description: str = ""
    position:    Tuple[int, int] | None = None      # (row, col)
