from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Tuple

class ButtonAction(Enum):
    SCRIPT   = "SCRIPT"
    LINK     = "LINK"
    GROUP    = "GROUP"
    FILE     = "FILE"
    EXPLORER = "EXPLORER"

@dataclass
class ButtonModel:
    """
    Datenklasse für einen GUI-Button.
    """
    id: str                         # Eindeutige Kennung
    label: str                      # Text auf dem Button
    action: ButtonAction            # Aktionstyp
    payload: str                    # Skriptpfad, URL o.Ä.
    icon: Path                      # Pfad zum Icon (relativ über util.paths.relative)
    size: Tuple[int, int] = (64, 64)     # Breite x Höhe in Pixeln
    position: Tuple[int, int] = (0, 0)   # X/Y-Koordinaten im Grid
    page: int = 1                   # Seite im Pagination-Stack
