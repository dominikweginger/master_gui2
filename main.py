#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication

def main():
    """
    Application‐Bootstrap: Erzeugt das QApplication‐Objekt
    und startet die Event‐Schleife.
    """
    app = QApplication(sys.argv)

    # TODO: Hier später das Hauptfenster importieren und anzeigen
    # from ui.master_window import MasterWindow
    # window = MasterWindow()
    # window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
