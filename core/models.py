from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Tuple, Optional


class ButtonAction(Enum):
    SCRIPT   = "SCRIPT"
    LINK     = "LINK"
    FILE     = "FILE"
    EXPLORER = "EXPLORER"
    MENU     = "MENU"        # ← NEU: öffnet Unterseite


@dataclass
class ButtonModel:
    """
    Datenklasse für einen GUI-Button.
    """
    id: str
    label: str
    action: ButtonAction
    icon: Path
    payload: str = ""
    parent_id: Optional[str] = None        # ← NEU
    size: Tuple[int, int] = (64, 64)
    position: Tuple[int, int] = (0, 0)     # wird zur Laufzeit gesetzt
