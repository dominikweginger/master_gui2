#!/usr/bin/env python3
"""
ui.button_editor
================
Modaler Dialog zum Erstellen oder Bearbeiten **eines** Buttons.
Wird von Button-Manager aufgerufen.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout
)

from core import storage
from util.paths import to_relative


class ButtonEditorDialog(QDialog):
    def __init__(
        self,
        config: dict,
        cfg_path: Path,
        parent_id: Optional[str] = None,
        edit_btn_id: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Button bearbeiten" if edit_btn_id else "Neuen Button anlegen")
        self.setModal(True)

        self._config = config
        self._cfg_path = cfg_path
        self._edit_mode = edit_btn_id is not None
        self._orig_id = edit_btn_id
        self._parent_id_default = parent_id

        # ---------------------------------------------------------------- Form-Felder
        self.name_edit = QLineEdit()
        self.action_cmb = QComboBox()
        self.action_cmb.addItems(["SCRIPT", "LINK", "FILE", "FOLDER", "MENU"])
        self.payload_edit = QLineEdit()
        self.payload_btn = QPushButton("…")
        self.icon_edit = QLineEdit("assets/icons/placeholder.png")
        self.icon_btn = QPushButton("…")
        self.menu_chk = QCheckBox("Als Haupt-Button (MENU) benutzen")
        self.desc_edit = QLineEdit()

        # Parent festlegen (nur Info – nicht editierbar; wird im Manager gesetzt)
        parent_lbl = QLabel(parent_id or "None")
        parent_lbl.setStyleSheet("color: grey;")
        parent_lbl.setToolTip("Übergeordnetes Element (wird im Baum gesetzt)")

        # ---------------------------------------------------------------- Layout
        lay = QFormLayout()
        lay.addRow("Name / ID:", self.name_edit)
        lay.addRow("Aktion:", self.action_cmb)

        payload_lay = QHBoxLayout()
        payload_lay.addWidget(self.payload_edit, 1)
        payload_lay.addWidget(self.payload_btn)
        lay.addRow("Pfad / URL:", payload_lay)

        icon_lay = QHBoxLayout()
        icon_lay.addWidget(self.icon_edit, 1)
        icon_lay.addWidget(self.icon_btn)
        lay.addRow("Icon:", icon_lay)

        lay.addRow("", self.menu_chk)
        lay.addRow("Beschreibung:", self.desc_edit)
        lay.addRow("Parent:", parent_lbl)

        # Dialog-Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)

        vbox = QVBoxLayout(self)
        vbox.addLayout(lay)
        vbox.addWidget(btn_box)

        # ---------------------------------------------------------------- Signals
        self.payload_btn.clicked.connect(self._browse_payload)
        self.icon_btn.clicked.connect(self._browse_icon)
        self.action_cmb.currentTextChanged.connect(self._toggle_payload_state)
        self.menu_chk.stateChanged.connect(self._on_menu_chk)

        # Bearbeiten → Felder vorfüllen
        if self._edit_mode:
            self._load_existing(edit_btn_id)
        else:
            self._toggle_payload_state(self.action_cmb.currentText())

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _toggle_payload_state(self, txt: str):
        is_menu = txt == "MENU" or self.menu_chk.isChecked()
        self.payload_edit.setEnabled(not is_menu)
        self.payload_btn.setEnabled(not is_menu)

    def _on_menu_chk(self, state: int):
        if state:
            self.action_cmb.setCurrentText("MENU")
        self._toggle_payload_state(self.action_cmb.currentText())

    def _browse_payload(self):
        a = self.action_cmb.currentText()
        if a in ("SCRIPT", "FILE"):
            fn, _ = QFileDialog.getOpenFileName(self, "Datei wählen", "", "Alle Dateien (*)")
        elif a == "FOLDER":
            fn = QFileDialog.getExistingDirectory(self, "Ordner wählen")
        else:  # LINK
            fn, ok = QFileDialog.getText(self, "URL eingeben", "https://…")
            if not ok:
                return
        if fn:
            self.payload_edit.setText(to_relative(fn))

    def _browse_icon(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Icon wählen", "assets/icons", "Bilder (*.png *.svg *.ico)")
        if fn:
            self.icon_edit.setText(to_relative(fn))

    # -------------------------------------------------------------------------
    def _on_save(self):
        btn_dict = {
            "id":          self.name_edit.text() or "Button",
            "label":       self.name_edit.text() or "Button",
            "action":      self.action_cmb.currentText(),
            "payload":     self.payload_edit.text() if self.payload_edit.isEnabled() else "",
            "icon":        self.icon_edit.text(),
            "parent":      self._parent_id_default,
            "description": self.desc_edit.text(),
        }
        # MENU-Buttons haben kein Payload
        if btn_dict["action"] == "MENU":
            btn_dict["payload"] = ""

        try:
            if self._edit_mode:
                storage.update_button(self._config, btn_dict)
            else:
                storage.add_button(self._config, btn_dict)
            storage.save_config(self._cfg_path, self._config)
            self.accept()
        except storage.StorageError as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Fehler", str(exc))

    # -------------------------------------------------------------------------
    def _load_existing(self, btn_id: str):
        btn = next(b for b in self._config["buttons"] if b["id"] == btn_id)
        self.name_edit.setText(btn["id"])
        self.action_cmb.setCurrentText(btn["action"])
        self.payload_edit.setText(btn.get("payload", ""))
        self.icon_edit.setText(btn["icon"])
        self.menu_chk.setChecked(btn["action"] == "MENU")
        self.desc_edit.setText(btn.get("description", ""))
        self._toggle_payload_state(btn["action"])
