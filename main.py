#!/usr/bin/env python3
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.storage import load_config, StorageError
from core.theming import apply_theme
from ui.master_window import MasterWindow

def main():
    # 1) Config laden
    try:
        config = load_config(Path("config.json"))
        print("⚡️ Config geladen:", config)
    except StorageError as e:
        print("❌ Konnte Config nicht laden:", e)
        return

    # 2) Qt-Anwendung initialisieren
    app = QApplication(sys.argv)

    # 2.1) QSS-Stylesheet laden
    apply_theme(config["theme"])

    # 3) Hauptfenster erzeugen
    window = MasterWindow(config)
    # 3.1) Hintergrundbild aus Config (via apply_background – QPalette)
    window.apply_background(config["theme"].get("background", ""))

    window.show()

    # 4) Event-Loop starten
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
