#!/usr/bin/env python3
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from core.storage import load_config, StorageError
from ui.master_window import MasterWindow

def main():
    # 1) Config laden
    try:
        config = load_config(Path("config.json"))
        print("⚡️ Config geladen:", config)
    except StorageError as e:
        print("❌ Konnte Config nicht laden:", e)
        return

    # 2) Qt-Applikation initialisieren
    app = QApplication(sys.argv)

    # 3) Hauptfenster erzeugen und anzeigen
    window = MasterWindow()
    window.show()

    # 4) Event-Loop starten
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
