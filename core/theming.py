#!/usr/bin/env python3
"""
core.theming
============

Lädt globales QSS-Stylesheet.
Hintergrund-Bilder werden per MasterWindow.apply_background() gesetzt.
"""
from pathlib import Path
from PySide6.QtWidgets import QApplication

def apply_theme(theme_cfg: dict) -> None:
    """
    Lädt das globale QSS-Stylesheet.
    """
    app = QApplication.instance()
    qss_path = Path(theme_cfg.get("stylesheet", ""))
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
