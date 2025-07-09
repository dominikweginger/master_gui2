#!/usr/bin/env python3
# ui/master_window.py

import sys
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGridLayout, QMessageBox
)
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import QUrl


class MasterWindow(QMainWindow):
    """
    Hauptfenster der Anwendung mit dynamischem Laden & Rendering der Buttons
    basierend auf der config["buttons"].
    """

    def __init__(self, config: dict):
        super().__init__()
        self.config = config

        # ——————————————
        # 1) Seiten-Container & GridLayouts anlegen
        # ——————————————
        max_page = max(b["page"] for b in self.config["buttons"])
        self.pages = QStackedWidget()
        self.page_layouts: dict[int, QGridLayout] = {}

        for page_idx in range(1, max_page + 1):
            container = QWidget()
            grid = QGridLayout(container)
            self.pages.addWidget(container)
            self.page_layouts[page_idx] = grid

        # ——————————————
        # Zentrales Widget & Layout
        # ——————————————
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.addWidget(self.pages)

        # ——————————————
        # Paginierungsleiste
        # ——————————————
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("← Vor")
        self.page_label = QLabel(self._label_text())
        self.next_btn = QPushButton("Nächste →")
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        main_layout.addLayout(pagination_layout)

        self.setCentralWidget(central)

        # ——————————————
        # Signale verbinden
        # ——————————————
        self.prev_btn.clicked.connect(self.go_previous)
        self.next_btn.clicked.connect(self.go_next)
        self.pages.currentChanged.connect(self.on_page_changed)

        # ——————————————
        # 2) Buttons aus Config laden
        # ——————————————
        self.load_buttons()
        self.update_buttons()

    def load_buttons(self):
        """
        Liest self.config["buttons"] und platziert für jede Konfiguration
        einen QPushButton im entsprechenden GridLayout.
        """
        for btn_cfg in self.config["buttons"]:
            page = btn_cfg["page"]
            row, col = btn_cfg["position"]

            btn = QPushButton(btn_cfg["label"])
            if icon_path := btn_cfg.get("icon"):
                btn.setIcon(QIcon(icon_path))
            btn.setToolTip(btn_cfg.get("tooltip", btn_cfg["label"]))
            btn.clicked.connect(lambda _, c=btn_cfg: self.handle_button_click(c))

            self.page_layouts[page].addWidget(btn, row, col)

    def handle_button_click(self, btn_cfg: dict):
        """
        Dispatcher für Button-Aktionen anhand von btn_cfg["action"].
        Unterstützte Aktionen: SCRIPT, LINK, EXPLORER, FILE, GROUP.
        """
        action = btn_cfg.get("action", "").upper()
        payload = btn_cfg.get("payload", "")

        try:
            if action == "SCRIPT":
                self.run_script(payload)

            elif action == "LINK":
                QDesktopServices.openUrl(QUrl(payload))

            elif action == "EXPLORER":
                path = Path(payload)
                if not path.exists():
                    raise FileNotFoundError(f"Pfad '{payload}' nicht gefunden.")
                if sys.platform.startswith("win"):
                    subprocess.Popen(["explorer", str(path)])
                else:
                    subprocess.Popen(["xdg-open", str(path)])

            elif action == "FILE":
                file = Path(payload)
                if not file.is_file():
                    raise FileNotFoundError(f"Datei '{payload}' nicht gefunden.")
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(file)))

            elif action == "GROUP":
                target = int(payload)
                self.pages.setCurrentIndex(target - 1)

            else:
                raise ValueError(f"Aktions-Typ '{action}' nicht implementiert.")

        except Exception as e:
            QMessageBox.critical(self, "Fehler bei Aktion", str(e))

    def run_script(self, script_path: str):
        """
        Führt ein externes Python-Skript im eigenen Interpreter aus.
        """
        script = Path(script_path)
        if not script.is_file():
            raise FileNotFoundError(f"Skript '{script_path}' nicht gefunden.")
        subprocess.Popen([sys.executable, str(script)], cwd=str(script.parent))

    def _label_text(self) -> str:
        """Hilfsfunktion für das Seiten-Label (Seite X / Y)."""
        return f"Seite {self.pages.currentIndex() + 1} / {self.pages.count()}"

    def on_page_changed(self, index: int):
        """Aktualisiert Label und Paginierungs-Buttons bei Seitenwechsel."""
        self.page_label.setText(self._label_text())
        self.update_buttons()

    def update_buttons(self):
        """Aktiviert/Deaktiviert die Vor-/Nächste-Buttons."""
        idx = self.pages.currentIndex()
        cnt = self.pages.count()
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < cnt - 1)

    def go_previous(self):
        """Wechselt zur vorherigen Seite."""
        idx = self.pages.currentIndex()
        if idx > 0:
            self.pages.setCurrentIndex(idx - 1)

    def go_next(self):
        """Wechselt zur nächsten Seite."""
        idx = self.pages.currentIndex()
        if idx < self.pages.count() - 1:
            self.pages.setCurrentIndex(idx + 1)
