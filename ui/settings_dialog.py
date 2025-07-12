#!/usr/bin/env python3
"""
ui.settings_dialog
==================
Dialog zum Ändern von Fenstertitel und Hintergrundbild.
"""
from pathlib import Path

from PySide6.QtCore    import Qt
from PySide6.QtGui     import QPixmap
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton,
    QLabel, QDialogButtonBox, QFileDialog, QVBoxLayout
)

from core import storage
from util.paths import to_relative
from .master_window import MasterWindow

class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, cfg_path: Path, parent: MasterWindow):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.cfg      = cfg
        self.cfg_path = cfg_path
        self.parent   = parent

        # Widgets
        self.title_edit = QLineEdit(cfg.get("window_title", parent.windowTitle()))
        self.bg_edit    = QLineEdit(cfg["theme"].get("background", ""))
        btn_browse     = QPushButton("…")
        btn_remove     = QPushButton("Entfernen")
        self.preview    = QLabel()
        self.preview.setFixedSize(200, 200)
        self.preview.setAlignment(Qt.AlignCenter)

        # Layout
        form = QFormLayout()
        form.addRow("Fenstertitel:", self.title_edit)

        sub = QVBoxLayout()
        row = QFormLayout()
        row.addRow("Bildpfad:", self.bg_edit)
        br = QVBoxLayout()
        br.addWidget(btn_browse)
        br.addWidget(btn_remove)
        row.addRow("", br)
        sub.addLayout(row)
        sub.addWidget(QLabel("Vorschau:"))
        sub.addWidget(self.preview)
        form.addRow(sub)

        btn_box = QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)

        main = QVBoxLayout(self)
        main.addLayout(form)
        main.addWidget(btn_box)

        # Signale
        btn_browse.clicked.connect(self._on_browse)
        btn_remove.clicked.connect(self._on_remove)  # <-- neu
        self.bg_edit.textChanged.connect(lambda _: self._set_background(self.bg_edit.text(), False))

        # Erste Vorschau
        self._set_background(self.bg_edit.text(), False)

    def _on_browse(self):
        fn, _ = QFileDialog.getOpenFileName(
            self, "Hintergrund auswählen", "", "Bilder (*.png *.jpg *.jpeg)"
        )
        if fn:
            self.bg_edit.setText(to_relative(fn))

    def _set_background(self, path: str, cleared: bool):
        p = Path(path)
        if not cleared and p.exists():
            pix = QPixmap(str(p)).scaled(
                self.preview.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview.setPixmap(pix)
        else:
            self.preview.clear()

    def _on_remove(self):
        """
        Sofort Hintergrund-Eintrag aus config.json löschen
        und Dialog schließen.
        """
        # 1) Config anpassen
        self.cfg["theme"]["background"] = ""
        # 2) Speichern
        storage.save_config(self.cfg_path, self.cfg)
        # 3) Parent live updaten
        self.parent.apply_background("")  
        # 4) Dialog schließen
        self.accept()

    def _on_save(self):
        # 1) Live-Anpassung des Titels
        new_title = self.title_edit.text().strip()
        self.parent.setWindowTitle(new_title)

        # 2) Live-Anpassung des Hintergrunds (falls noch nicht gelöscht)
        bg = self.bg_edit.text().strip()
        self.parent.apply_background(bg)

        # 3) Persistenz
        self.cfg["window_title"]        = new_title
        self.cfg["theme"]["background"] = bg
        storage.save_config(self.cfg_path, self.cfg)
        self.accept()
