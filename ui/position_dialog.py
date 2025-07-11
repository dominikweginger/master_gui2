#!/usr/bin/env python3
"""
ui.position_dialog
==================
Drag-&-Drop-Raster (5 × 6).  Speichert row/col erst nach Save in config.json.
"""
from __future__ import annotations
from pathlib import Path
from typing   import List, Dict, Tuple, Optional

from PySide6.QtCore    import Qt, QPoint, QMimeData
from PySide6.QtGui     import QDrag
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QGridLayout, QLabel, QPushButton, QWidget
)

from core import storage

GRID_ROWS = 5
GRID_COLS = 6


class SlotWidget(QLabel):
    """Grau hinterlegter Platzhalter für leere Slots."""
    def __init__(self):
        super().__init__(" ")
        self.setStyleSheet("background: #efefef; border: 1px dashed #bbb;")
        self.setFixedSize(80, 80)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, evt):
        evt.acceptProposedAction()

    def dropEvent(self, evt):
        """Verschiebe beim Drop einen Button hierher und lege am alten Platz wieder einen Slot."""
        btn_id = evt.mimeData().text()
        parent = self.parent()
        src = parent._btn_by_id(btn_id)
        if not src:
            return

        # alte Position ermitteln
        old_idx = parent._grid_layout.indexOf(src)
        old_r, old_c, _, _ = parent._grid_layout.getItemPosition(old_idx)
        # neue Position (dieser Slot)
        new_idx = parent._grid_layout.indexOf(self)
        new_r, new_c, _, _ = parent._grid_layout.getItemPosition(new_idx)

        # Slot ersetzen durch Button
        self.deleteLater()
        parent._grid_layout.addWidget(src, new_r, new_c)
        # am alten Platz neuen Slot nachziehen
        parent._grid_layout.addWidget(SlotWidget(), old_r, old_c)

        # temp-Map aktualisieren
        parent._temp_pos[src.cfg_btn["id"]] = {"row": new_r, "col": new_c}
        evt.acceptProposedAction()


class DraggableButton(QPushButton):
    def __init__(self, cfg_btn: dict):
        super().__init__(cfg_btn["id"])
        self.cfg_btn = cfg_btn
        self.setFixedSize(80, 80)
        self.setAcceptDrops(True)

    # Drag-Start
    def mouseMoveEvent(self, evt):
        if evt.buttons() != Qt.LeftButton:
            return
        drag = QDrag(self)
        mime = QMimeData()
        drag.setMimeData(mime)
        mime.setText(self.cfg_btn["id"])
        drag.exec(Qt.MoveAction)

    # Drop-Target für Button-zu-Button Tausch
    def dragEnterEvent(self, evt):
        evt.acceptProposedAction()

    def dropEvent(self, evt):
        source_id = evt.mimeData().text()
        src = self.parent()._btn_by_id(source_id)
        dst = self
        if not src or src is dst:
            return
        self.parent()._swap_buttons(src, dst)
        evt.acceptProposedAction()


class PositionDialog(QDialog):
    def __init__(self, cfg: dict, cfg_path: Path, level_buttons: List[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buttons positionieren")
        self._cfg           = cfg
        self._cfg_path      = cfg_path
        self._level_buttons = level_buttons

        # temp-Map initial aus altem Config befüllen
        self._temp_pos: Dict[str, Optional[dict]] = {
            b["id"]: b.get("position") for b in level_buttons
        }

        self._grid_layout = QGridLayout()
        self._setup_grid()

        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)

        vbox = QGridLayout(self)
        vbox.addLayout(self._grid_layout, 0, 0)
        vbox.addWidget(btn_box,      1, 0)

    def _btn_by_id(self, bid: str) -> Optional[DraggableButton]:
        for i in range(self._grid_layout.count()):
            w = self._grid_layout.itemAt(i).widget()
            if isinstance(w, DraggableButton) and w.cfg_btn["id"] == bid:
                return w
        return None

    def _pos_valid(self, pos: Optional[dict]) -> bool:
        """Nur gültige Positionen verwenden (row und col müssen ints sein)."""
        return (
            isinstance(pos, dict)
            and isinstance(pos.get("row"), int)
            and isinstance(pos.get("col"), int)
        )

    def _setup_grid(self):
        # 1) bereits vorhandene gültige Positionen merken
        taken: Dict[Tuple[int,int], dict] = {}
        for btn_id, pos in self._temp_pos.items():
            if self._pos_valid(pos):
                taken[(pos["row"], pos["col"])] = next(
                    b for b in self._level_buttons if b["id"] == btn_id
                )

        # 2) Raster initial füllen (Buttons + leere Slots)
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if (r, c) in taken:
                    cfg_btn = taken[(r, c)]
                    self._grid_layout.addWidget(DraggableButton(cfg_btn), r, c)
                else:
                    self._grid_layout.addWidget(SlotWidget(), r, c)

        # 3) JEDEN unpositionierten Button in erstbesten freien Slot setzen (KORRIGIERT)
        unplaced_buttons = iter([
            b for b in self._level_buttons
            if not self._pos_valid(self._temp_pos.get(b["id"]))
        ])
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                widget = self._grid_layout.itemAtPosition(r, c).widget()
                if isinstance(widget, SlotWidget):
                    try:
                        button_to_place = next(unplaced_buttons)
                    except StopIteration:
                        return
                    widget.deleteLater()
                    self._grid_layout.addWidget(DraggableButton(button_to_place), r, c)
                    # temp-Map aktualisieren
                    self._temp_pos[button_to_place["id"]] = {"row": r, "col": c}

    def _swap_buttons(self, src_btn: DraggableButton, dst_btn: DraggableButton):
        # Positionen auslesen
        src_pos = self._grid_layout.getItemPosition(
            self._grid_layout.indexOf(src_btn)
        )[:2]
        dst_pos = self._grid_layout.getItemPosition(
            self._grid_layout.indexOf(dst_btn)
        )[:2]
        # Widgets tauschen
        self._grid_layout.removeWidget(src_btn)
        self._grid_layout.removeWidget(dst_btn)
        self._grid_layout.addWidget(src_btn, *dst_pos)
        self._grid_layout.addWidget(dst_btn, *src_pos)
        # temp-Map aktualisieren
        self._temp_pos[src_btn.cfg_btn["id"]] = {"row": dst_pos[0], "col": dst_pos[1]}
        self._temp_pos[dst_btn.cfg_btn["id"]] = {"row": src_pos[0], "col": src_pos[1]}

    def _on_save(self):
        # erst beim Save zurück ins echte Config-Objekt schreiben
        for btn in self._level_buttons:
            pos = self._temp_pos.get(btn["id"])
            if self._pos_valid(pos):
                btn["position"] = pos
        storage.save_config(self._cfg_path, self._cfg)
        self.accept()
