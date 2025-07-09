#!/usr/bin/env python3
"""
GUI-Hauptfenster – Version 2025-07-09
* 5×6-Raster (30 Buttons) pro Seite
* beliebige Hierarchietiefe über parent-Feld
* Breadcrumb mit  🏠  und  ⬅  Buttons
"""

import sys, subprocess
from collections import defaultdict
from pathlib import Path
from typing import Tuple, List, Dict

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGridLayout, QMessageBox, QFrame
)
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import QUrl

GRID_ROWS, GRID_COLS = 5, 6
MAX_PER_PAGE = GRID_ROWS * GRID_COLS


class MasterWindow(QMainWindow):
    # ----------------------------------------------------------
    # Initialisierung
    # ----------------------------------------------------------
    def __init__(self, config: dict):
        super().__init__()
        self.cfg_buttons: List[dict] = config["buttons"]

        # --- Baum aufbauen ---------------------------------------------------
        self.children: Dict[str | None, List[dict]] = defaultdict(list)
        for b in self.cfg_buttons:
            self.children[b["parent"]].append(b)

        # --- Widgets ---------------------------------------------------------
        self.pages          = QStackedWidget()
        self.page_for_id    = {}      # parent-ID  → erste Seite seiner Children
        self.nav_stack      = []      # Verlauf von parent-IDs (für Breadcrumb)

        self._build_pages()           # alle Seiten erzeugen

        central     = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.addWidget(self.pages)

        # -------- Breadcrumb -------------------------------------------------
        bc_frame = QFrame()
        bc_frame.setFrameShape(QFrame.StyledPanel)
        self.bc_layout = QHBoxLayout(bc_frame)

        self.btn_home = QPushButton("🏠 Startseite")
        self.btn_up   = QPushButton("⬅ Zurück")
        self.btn_home.clicked.connect(self._go_home)
        self.btn_up.clicked.connect(self._go_up)
        self.bc_layout.addWidget(self.btn_home)
        self.bc_layout.addWidget(self.btn_up)

        main_layout.insertWidget(1, bc_frame)

        # -------- Pagination -------------------------------------------------
        self.prev_btn = QPushButton("← Vor")
        self.next_btn = QPushButton("Nächste →")
        self.page_lbl = QLabel("")
        pagel = QHBoxLayout()
        pagel.addWidget(self.prev_btn)
        pagel.addWidget(self.page_lbl)
        pagel.addWidget(self.next_btn)
        main_layout.addLayout(pagel)

        self.prev_btn.clicked.connect(self._go_prev)
        self.next_btn.clicked.connect(self._go_next)
        self.pages.currentChanged.connect(self._page_changed)

        self.setCentralWidget(central)
        self._update_breadcrumb()
        self._update_pagination()

    # ----------------------------------------------------------
    # Seitenerzeugung
    # ----------------------------------------------------------
    def _new_grid_page(self) -> Tuple[QWidget, QGridLayout]:
        container = QWidget()
        grid = QGridLayout(container)
        self.pages.addWidget(container)
        return container, grid

    def _add_cfg_button(self, grid: QGridLayout, cfg: dict):
        row, col = divmod(grid.count(), GRID_COLS)
        btn = QPushButton(cfg["label"])
        if icon := cfg.get("icon"):
            btn.setIcon(QIcon(icon))
        btn.clicked.connect(lambda _=None, b=cfg: self._on_button_click(b))
        grid.addWidget(btn, row, col)

    def _paginate_buttons(self, buttons: List[dict]) -> List[QWidget]:
        pages: List[QWidget] = []
        container, grid = self._new_grid_page()
        pages.append(container)

        for cfg in buttons:
            if grid.count() >= MAX_PER_PAGE:
                container, grid = self._new_grid_page()
                pages.append(container)
            self._add_cfg_button(grid, cfg)

        return pages  # Liste der Container-Widgets

    def _build_pages(self):
        # 1) Root-Seiten (parent = None)
        root_pages = self._paginate_buttons(self.children[None])

        # 2) Child-Seiten für jeden MENU-Knopf
        for parent_cfg in self.children[None]:
            if parent_cfg["action"] != "MENU":
                continue
            pages = self._paginate_buttons(self.children[parent_cfg["id"]])
            if pages:
                self.page_for_id[parent_cfg["id"]] = self.pages.indexOf(pages[0])

        # 3) Rekursion für tiefere Ebenen
        stack = list(self.children[None])  # shallow copy
        while stack:
            parent = stack.pop()
            childs = self.children[parent["id"]]
            for c in childs:
                if c["action"] == "MENU":
                    pages = self._paginate_buttons(self.children[c["id"]])
                    if pages:
                        self.page_for_id[c["id"]] = self.pages.indexOf(pages[0])
                    stack.append(c)

    # ----------------------------------------------------------
    # Breadcrumb
    # ----------------------------------------------------------
    def _update_breadcrumb(self):
        # alte Pfad-Buttons entfernen
        while self.bc_layout.count() > 2:
            w = self.bc_layout.takeAt(2).widget()
            w.deleteLater()

        # neue Pfad-Buttons erzeugen
        for depth, pid in enumerate(self.nav_stack):
            label = next(b["label"] for b in self.cfg_buttons if b["id"] == pid)
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=None, d=depth: self._jump_depth(d))
            self.bc_layout.addWidget(btn)

        self.btn_up.setEnabled(bool(self.nav_stack))

    # ----------------------------------------------------------
    # Button-Handler
    # ----------------------------------------------------------
    def _on_button_click(self, cfg: dict):
        act = cfg["action"]
        if act == "MENU":
            self.nav_stack.append(cfg["id"])
            self.pages.setCurrentIndex(self.page_for_id[cfg["id"]])
            self._update_breadcrumb()
            self._update_pagination()
            return

        try:
            if act == "SCRIPT":
                subprocess.Popen([sys.executable, cfg["payload"]])
            elif act == "LINK":
                QDesktopServices.openUrl(QUrl(cfg["payload"]))
            elif act == "FILE":
                QDesktopServices.openUrl(QUrl.fromLocalFile(cfg["payload"]))
            elif act == "EXPLORER":
                subprocess.Popen(["explorer", cfg["payload"]])
        except Exception as exc:
            QMessageBox.critical(self, "Fehler", str(exc))

    # ---------- Breadcrumb-Buttons ----------
    def _go_home(self):
        self.nav_stack.clear()
        self.pages.setCurrentIndex(0)
        self._update_breadcrumb()
        self._update_pagination()

    def _go_up(self):
        if self.nav_stack:
            self.nav_stack.pop()
            target = 0 if not self.nav_stack else self.page_for_id[self.nav_stack[-1]]
            self.pages.setCurrentIndex(target)
            self._update_breadcrumb()
            self._update_pagination()

    def _jump_depth(self, depth: int):
        self.nav_stack = self.nav_stack[:depth + 1]
        target = self.page_for_id[self.nav_stack[-1]]
        self.pages.setCurrentIndex(target)
        self._update_breadcrumb()
        self._update_pagination()

    # ---------- Pfeil-Navigation ----------
    def _level_bounds(self) -> Tuple[int, int]:
        """liefert (erste, letzte) Page-Index der aktuellen Ebene"""
        first = 0 if not self.nav_stack else self.page_for_id[self.nav_stack[-1]]
        btns = self.children[self.nav_stack[-1] if self.nav_stack else None]
        pages = (len(btns) - 1) // MAX_PER_PAGE + 1
        return first, first + pages - 1

    def _go_prev(self):
        first, _ = self._level_bounds()
        idx = self.pages.currentIndex()
        if idx > first:
            self.pages.setCurrentIndex(idx - 1)

    def _go_next(self):
        _, last = self._level_bounds()
        idx = self.pages.currentIndex()
        if idx < last:
            self.pages.setCurrentIndex(idx + 1)

    def _page_changed(self, _):
        self._update_pagination()

    def _update_pagination(self):
        first, last = self._level_bounds()
        idx = self.pages.currentIndex()
        self.prev_btn.setEnabled(idx > first)
        self.next_btn.setEnabled(idx < last)
        self.page_lbl.setText(f"Seite {idx + 1} / {self.pages.count()}")
