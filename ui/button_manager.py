#!/usr/bin/env python3
"""
ui.button_manager
=================
Zentrales Fenster mit einem QTreeWidget, in dem alle Buttons
hierarchisch angezeigt und via Kontext-Buttons bearbeitet werden.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore    import Qt
from PySide6.QtGui     import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QHBoxLayout
)

from core import storage

from .button_editor    import ButtonEditorDialog
from .position_dialog  import PositionDialog, SlotWidget, GRID_ROWS, GRID_COLS
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel

class ButtonManager(QDialog):
    def __init__(self, cfg: dict, cfg_path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Button-Manager")
        self.resize(500, 600)
        self._cfg      = cfg
        self._cfg_path = cfg_path

        # ------------------------------ Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name / ID"])
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.itemDoubleClicked.connect(self._on_edit)
        self._reload_tree()

        # ------------------------------ Buttons
        btn_new      = QPushButton("Neu")
        btn_edit     = QPushButton("Bearbeiten")
        btn_delete   = QPushButton("Löschen")
        btn_position = QPushButton("Verschieben")
        btn_new.clicked.connect(self._on_new)
        btn_edit.clicked.connect(self._on_edit)
        btn_delete.clicked.connect(self._on_delete)
        btn_position.clicked.connect(self._on_position)

        hbox = QHBoxLayout()
        hbox.addWidget(btn_new)
        hbox.addWidget(btn_edit)
        hbox.addWidget(btn_delete)
        hbox.addWidget(btn_position)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.tree)
        vbox.addLayout(hbox)
        vbox.addWidget(QLabel("Positions-Vorschau der aktuellen Ebene:"))
        # Rahmen und GridContainer
        self._preview_frame  = QFrame(self)
        self._preview_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self._preview_layout = QGridLayout(self._preview_frame)
        self._preview_layout.setSpacing(4)
        vbox.addWidget(self._preview_frame)
        # Dynamisch aktualisieren, wenn Auswahl im Baum wechselt
        self.tree.itemSelectionChanged.connect(self._update_preview)
        # erste Befüllung
        self._update_preview()

    # -------------------------------------------------------------------------
    def _reload_tree(self):
        self.tree.clear()
        roots: List[dict] = [b for b in self._cfg["buttons"] if b["parent"] is None]
        for b in roots:
            self._add_item_recursive(None, b)

    def _add_item_recursive(self, parent_item: Optional[QTreeWidgetItem], cfg_btn: dict):
        item = QTreeWidgetItem([cfg_btn["id"]])
        item.setData(0, Qt.UserRole, cfg_btn["id"])
        if parent_item:
            parent_item.addChild(item)
        else:
            self.tree.addTopLevelItem(item)
        # rekursiv alle Kinder
        for c in [b for b in self._cfg["buttons"] if b["parent"] == cfg_btn["id"]]:
            self._add_item_recursive(item, c)

    # -------------------------------------------------------------------------
    def _current_ids(self) -> List[str]:
        return [
            it.data(0, Qt.UserRole)
            for it in self.tree.selectedItems()
        ]

    # -------------------------------------------------------------------------
    def _on_new(self):
        parent_ids = self._current_ids()
        parent_id  = parent_ids[0] if parent_ids else None

        # ── Blockiere Child-Anlage, wenn Parent keine MENU-Action hat ──
        if parent_id:
            parent_cfg = next(
                (b for b in self._cfg["buttons"] if b["id"] == parent_id),
                None
            )
            if parent_cfg and parent_cfg.get("action") != "MENU":
                QMessageBox.warning(
                    self,
                    "Ungültiger Parent-Button",
                    f"Ein Button mit Aktion '{parent_cfg['action']}' darf keine Unterpunkte haben.\n"
                    "Aktiviere zuerst 'Als Haupt-Button (MENU)' für diesen Button."
                )
                return

        # Wenn alles ok, Dialog öffnen
        dlg = ButtonEditorDialog(self._cfg, self._cfg_path, parent_id, parent=None)
        if dlg.exec():
            self._reload_tree()

    # -------------------------------------------------------------------------
    def _on_edit(self, *_):
        ids = self._current_ids()
        if not ids:
            return
        dlg = ButtonEditorDialog(self._cfg, self._cfg_path, None, ids[0], parent=self)
        if dlg.exec():
            self._reload_tree()

    # -------------------------------------------------------------------------
    def _on_delete(self):
        ids = self._current_ids()
        if not ids:
            return
        # ... (bestehende Lösch-Logik unverändert) ...
        for bid in ids:
            storage.delete_button_recursive(self._cfg, bid)
        storage.save_config(self._cfg_path, self._cfg)
        self._reload_tree()

    # -------------------------------------------------------------------------
    def _on_position(self):
        ids = self._current_ids()
        if not ids:
            return
        # Positioniert wird IMMER die ganze Ebene (Parent der Auswahl)
        level_parent = None if not ids else next(
            b for b in self._cfg["buttons"] if b["id"] == ids[0]
        )["parent"]
        same_level = [b for b in self._cfg["buttons"] if b["parent"] == level_parent]

        dlg = PositionDialog(self._cfg, self._cfg_path, same_level, parent=self)
        if dlg.exec():
            self._reload_tree()

    def _update_preview(self):
        """Zeigt alle Buttons der gerade selektierten Ebene im 5×6-Raster an."""
        # 1) Alte Widgets entfernen
        for i in reversed(range(self._preview_layout.count())):
            w = self._preview_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # 2) Welche Ebene? (wie in _on_position)
        ids = self._current_ids()
        level_parent = None
        if ids:
            # Parent des ersten ausgewählten Buttons
            level_parent = next(
                b for b in self._cfg["buttons"]
                if b["id"] == ids[0]
            )["parent"]

        # 3) Alle Buttons dieser Ebene sammeln
        level_buttons = [
            b for b in self._cfg["buttons"]
            if b.get("parent") == level_parent
        ]

        # 4) Mapping position → Button-Dict
        taken = {
            (b["position"]["row"], b["position"]["col"]): b
            for b in level_buttons
            if "position" in b
        }

        # 5) 5×6-Raster befüllen
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if (r, c) in taken:
                    # gefülltes Feld: Button-ID als Label
                    lbl = QLabel(taken[(r, c)]["id"])
                    lbl.setAlignment(Qt.AlignCenter)
                    lbl.setFrameStyle(QFrame.Panel | QFrame.Raised)
                    self._preview_layout.addWidget(lbl, r, c)
                else:
                    # freier Slot (grau gestrichelt)
                    self._preview_layout.addWidget(SlotWidget(), r, c)

