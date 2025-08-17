#!/usr/bin/env python3
"""
ui.master_window
================
Hauptfenster der Anwendung. Zeigt Buttons aus *config.json*,
öffnet Task-Dashboard, den Button-Manager und besitzt eine
Toolbar für Menü-Navigation sowie eine statische Pagination
mit Prev/Next und Seitenanzeige unten.

NEU (Patch B):
- payloads werden vor der Ausführung in absolute Pfade aufgelöst (to_absolute)
- SCRIPT-Start: im EXE-Modus (sys.frozen) via os.startfile, sonst via Python-Interpreter
"""
from __future__ import annotations

import os
import subprocess, sys
from pathlib import Path
from typing import Dict, List, Tuple

from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui  import QAction, QDesktopServices, QIcon, QKeySequence, QPalette, QBrush, QPixmap
from PySide6.QtWidgets import (
    QLabel, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QApplication
)

from core import storage
from ui.task_dashboard import TaskDashboard
from ui.button_manager import ButtonManager
from util.paths import to_absolute  # NEU

# -------------------------------------------------------------------
GRID_ROWS    = 5
GRID_COLS    = 6
MAX_PER_PAGE = GRID_ROWS * GRID_COLS  # 30 Buttons pro Seite

# -------------------------------------------------------------------
class MasterWindow(QMainWindow):
    """Zentrales Hauptfenster der Master-GUI mit statischer Pagination."""
    def __init__(self, config: dict, cfg_path: Path | str = Path("config.json")):
        super().__init__()

        # Persistente Config
        self.cfg      = config
        self.cfg_path = Path(cfg_path)

        # Fenstertitel aus Config oder Default
        self.setWindowTitle(self.cfg.get("window_title", "Master GUI"))

        # Pagination-Datenstrukturen
        self.pages_for_parent: Dict[str|None, List[QWidget]] = {}
        self.current_page_idx: Dict[str|None, int] = {}

        # QStackedWidget für alle Seiten aller Ebenen
        self.pages: QStackedWidget = QStackedWidget()
        self.page_for_id: Dict[Tuple[str|None,int], QWidget] = {}
        self.nav_stack: List[str|None] = [None]

        # Layout-Aufbau
        central = QWidget()
        vbox    = QVBoxLayout(central)
        vbox.addWidget(self.pages)

        # === Pagination-Controls unten ===
        self.prev_btn   = QPushButton("‹‹ Prev")
        self.next_btn   = QPushButton("Next ››")
        self.page_label = QLabel()
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        self.next_btn.clicked.connect(self._on_next_clicked)

        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        vbox.addWidget(nav_widget)
        # === Ende Pagination-Controls ===

        # Breadcrumb oberhalb
        self._breadcrumb = QLabel()
        vbox.addWidget(self._breadcrumb)

        self.setCentralWidget(central)

        # Task-Dashboard & Menü-Toolbar
        self.dashboard = TaskDashboard(self)
        self._init_menu_and_toolbar()

        # Erste Seiten erzeugen und anzeigen
        self._rebuild_pages()

    # -----------------------------------------------------------------
    def _init_menu_and_toolbar(self) -> None:
        """Menü- und Toolbar-Einträge (bleiben unverändert)."""
        menu = self.menuBar()
        menu.addAction("Task-Dashboard", self.dashboard.show)
        menu.addAction("Button-Manager", self._open_manager)

        nav_tb = self.addToolBar("Navigation")
        nav_tb.setMovable(False)

        # ← Zurück
        self.act_back = QAction("← Zurück", self)
        self.act_back.setShortcut(QKeySequence(Qt.Key_Backspace))
        self.act_back.setEnabled(False)
        self.act_back.triggered.connect(self._go_back)
        nav_tb.addAction(self.act_back)

        # ⏭ Start
        self.act_home = QAction("⏭ Start", self)
        self.act_home.setShortcut(QKeySequence(Qt.Key_Home))
        self.act_home.triggered.connect(self._go_home)
        nav_tb.addAction(self.act_home)

        # ── NEU: Einstellungen
        act_settings = QAction("Einstellungen", self)
        act_settings.triggered.connect(self._open_settings)
        nav_tb.addAction(act_settings)

    # -----------------------------------------------------------------
    def _children_of(self, parent_id: str|None):
        """Alle Buttons in config, deren parent == parent_id."""
        return [b for b in self.cfg["buttons"] if b["parent"] == parent_id]

    # -----------------------------------------------------------------
    def _rebuild_pages(self) -> None:
        """
        Baut für jedes Menü-Level (parent_id) statisch so viele
        Seiten à MAX_PER_PAGE Buttons, wie benötigt.
        """
        self.nav_stack = [None]
        self.pages_for_parent.clear()
        self.page_for_id.clear()

        while self.pages.count():
            w = self.pages.widget(0)
            self.pages.removeWidget(w)
            w.deleteLater()

        def make_pages_for(parent_id: str|None) -> List[QWidget]:
            children = self._children_of(parent_id)
            children.sort(key=lambda b: (
                b.get("position",{}).get("row", MAX_PER_PAGE),
                b.get("position",{}).get("col", MAX_PER_PAGE),
            ))
            pages: List[QWidget] = []
            for i in range(0, len(children), MAX_PER_PAGE):
                chunk = children[i:i+MAX_PER_PAGE]
                page  = QWidget()
                grid  = QGridLayout(page)
                for idx, cfg_btn in enumerate(chunk):
                    if "position" in cfg_btn:
                        r = cfg_btn["position"]["row"]
                        c = cfg_btn["position"]["col"]
                    else:
                        r, c = divmod(idx, GRID_COLS)
                    btn = QPushButton(cfg_btn["id"])
                    if ico := cfg_btn.get("icon"):
                        icon = QIcon(ico)
                        btn.setIcon(icon)
                        sz  = icon.availableSizes()
                        btn.setIconSize(sz[0] if sz else QSize(64,64))
                    if desc := cfg_btn.get("description"):
                        btn.setToolTip(desc)
                    btn.clicked.connect(lambda _, b=cfg_btn: self._on_click(b))
                    grid.addWidget(btn, r, c)
                pages.append(page)
            return pages

        all_parents = [None] + [b["id"] for b in self.cfg["buttons"] if b["action"]=="MENU"]
        for pid in all_parents:
            page_list = make_pages_for(pid)
            self.pages_for_parent[pid] = page_list
            self.current_page_idx[pid] = 0
            for idx, pg in enumerate(page_list):
                self.page_for_id[(pid, idx)] = pg
                self.pages.addWidget(pg)

        # --- Fallback: Leere Startseite anlegen, wenn keine Buttons vorhanden sind ---
        if (None, 0) not in self.page_for_id:
            empty_page = QWidget()
            self.page_for_id[(None, 0)] = empty_page
            self.pages.addWidget(empty_page)
            self.pages_for_parent[None] = [empty_page]
            self.current_page_idx[None] = 0

        self.pages.setCurrentWidget(self.page_for_id[(None, 0)])
        self.act_back.setEnabled(False)
        self._update_breadcrumb()
        self._update_pagination_controls()

    # -----------------------------------------------------------------
    def _update_pagination_controls(self) -> None:
        pid   = self.nav_stack[-1]
        idx   = self.current_page_idx[pid]
        total = len(self.pages_for_parent[pid])
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < total - 1)
        self.page_label.setText(f"Seite {idx+1} von {total}")

    # -----------------------------------------------------------------
    def _on_prev_clicked(self) -> None:
        pid = self.nav_stack[-1]
        idx = self.current_page_idx[pid]
        if idx > 0:
            self.current_page_idx[pid] -= 1
            self.pages.setCurrentWidget(self.page_for_id[(pid, idx-1)])
            self._update_pagination_controls()

    # -----------------------------------------------------------------
    def _on_next_clicked(self) -> None:
        pid = self.nav_stack[-1]
        idx = self.current_page_idx[pid]
        if idx < len(self.pages_for_parent[pid]) - 1:
            self.current_page_idx[pid] += 1
            self.pages.setCurrentWidget(self.page_for_id[(pid, idx+1)])
            self._update_pagination_controls()

    # -----------------------------------------------------------------
    def _on_click(self, cfg: dict) -> None:
        act = cfg["action"]

        if act == "MENU":
            self.nav_stack.append(cfg["id"])
            self.current_page_idx[cfg["id"]] = 0
            self.pages.setCurrentWidget(self.page_for_id[(cfg["id"], 0)])
            self._update_breadcrumb()
            self.act_back.setEnabled(True)
            self._update_pagination_controls()
            return

        # --- NEU: payload immer absolut auflösen ---
        payload = cfg.get("payload") or ""
        payload_abs = str(to_absolute(payload)) if payload else ""

        if act == "SCRIPT":
            # Dev: über Python-Interpreter; EXE: über Dateiverknüpfung (py.exe/pythonw)
            if getattr(sys, "frozen", False):
                try:
                    os.startfile(payload_abs)  # Windows: startet .py mit verknüpfter Python-Installation
                except OSError:
                    # Fallback: py-Launcher versuchen (falls vorhanden)
                    subprocess.Popen(["py", "-3", payload_abs], shell=False)
            else:
                subprocess.Popen([sys.executable, payload_abs], shell=False)

        elif act == "FILE":
            # Datei im Standardprogramm öffnen
            if sys.platform.startswith("win"):
                os.startfile(payload_abs)
            else:
                subprocess.Popen([payload_abs], shell=False)

        elif act == "LINK":
            QDesktopServices.openUrl(QUrl(cfg["payload"]))

        elif act == "FOLDER":
            # Explorer mit absolutem Pfad
            subprocess.Popen(f'explorer "{payload_abs}"')

    # -----------------------------------------------------------------
    def _go_back(self) -> None:
        if len(self.nav_stack) <= 1:
            return
        self.nav_stack.pop()
        pid = self.nav_stack[-1]
        self.current_page_idx[pid] = 0
        self.pages.setCurrentWidget(self.page_for_id[(pid, 0)])
        self._update_breadcrumb()
        self.act_back.setEnabled(len(self.nav_stack) > 1)
        self._update_pagination_controls()

    # -----------------------------------------------------------------
    def _go_home(self) -> None:
        self.nav_stack = [None]
        self.current_page_idx[None] = 0
        self.pages.setCurrentWidget(self.page_for_id[(None, 0)])
        self._update_breadcrumb()
        self.act_back.setEnabled(False)
        self._update_pagination_controls()

    # -----------------------------------------------------------------
    def _update_breadcrumb(self) -> None:
        crumbs = ["Start"] + self.nav_stack[1:]
        self._breadcrumb.setText(" / ".join(crumbs))

    # -----------------------------------------------------------------
    def _open_manager(self) -> None:
        dlg = ButtonManager(self.cfg, self.cfg_path, self)
        if dlg.exec():
            storage.save_config(self.cfg_path, self.cfg)
            self._rebuild_pages()

    # -----------------------------------------------------------------
    def _open_settings(self) -> None:
        """Öffnet den Settings-Dialog, um Titel und Hintergrund zu ändern."""
        from .settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.cfg, self.cfg_path, self)
        dlg.exec()

    # -----------------------------------------------------------------
    def apply_background(self, bg_path: str) -> None:
        """
        Setzt das Hintergrundbild nur auf das centralWidget via QPalette,
        ohne Buttons oder Toolbars zu überdecken.
        Ein leerer oder ungültiger Pfad entfernt den Hintergrund wieder.
        """
        cw = self.centralWidget()
        if bg_path and Path(bg_path).exists():
            pix = QPixmap(str(Path(bg_path)))
            pal = cw.palette()
            pal.setBrush(QPalette.Window, QBrush(pix))
            cw.setAutoFillBackground(True)
            cw.setPalette(pal)
        else:
            cw.setAutoFillBackground(False)
            # stylesheet bzw. Palette-Default wiederherstellen
            cw.setPalette(QApplication.instance().palette())
