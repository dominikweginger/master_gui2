#!/usr/bin/env python3
"""
ui.master_window
================
Hauptfenster der Anwendung.  Zeigt Buttons aus *config.json*,
öffnet Task-Dashboard, den Button-Manager **und** besitzt jetzt eine
Navigation-Toolbar mit

* **← Zurück** – springt exakt **eine** Ebene höher
* **⏭ Start**   – springt direkt zur Root-Ebene

Alle bisherigen Features bleiben unverändert.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui  import (
    QAction,
    QDesktopServices,
    QIcon,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

from core import storage
from ui.task_dashboard import TaskDashboard
from ui.button_manager import ButtonManager

# -----------------------------------------------------------------------------
GRID_ROWS      = 5
GRID_COLS      = 6
MAX_PER_PAGE   = GRID_ROWS * GRID_COLS

# -----------------------------------------------------------------------------
class MasterWindow(QMainWindow):
    """Zentrales Hauptfenster der Master-GUI."""

    # ---------------------------------------------------------------------
    #   Initialisierung
    # ---------------------------------------------------------------------
    def __init__(self, config: dict, cfg_path: Path | str = Path("config.json")):
        super().__init__()
        self.setWindowTitle("Master GUI")

        # ---------------- Persistente Config -----------------------------
        self.cfg      = config
        self.cfg_path = Path(cfg_path)

        # ---------------- Navigation / Seiten ----------------------------
        self.pages:       QStackedWidget        = QStackedWidget()
        self.page_for_id: Dict[str | None, QWidget] = {}
        self.nav_stack:   List[str | None]      = [None]           # Root-Ebene

        # ---------------- Zentrales Layout -------------------------------
        central = QWidget()
        vbox    = QVBoxLayout(central)
        vbox.addWidget(self.pages)
        self._breadcrumb = QLabel()
        vbox.addWidget(self._breadcrumb)
        self.setCentralWidget(central)

        # ---------------- Task-Dashboard -------------------------------
        self.dashboard = TaskDashboard(self)

        # ---------------- Menü-Bar & Toolbar -----------------------------
        self._init_menu_and_toolbar()

        # ---------------- Erste Seiten erzeugen --------------------------
        self._rebuild_pages()

    # ------------------------------------------------------------------
    #   Toolbar-Helfer
    # ------------------------------------------------------------------
    def _init_menu_and_toolbar(self) -> None:
        """Erstellt Menü-Einträge und die Navigation-Toolbar."""
        menu = self.menuBar()
        menu.addAction("Task-Dashboard", self.dashboard.show)
        menu.addAction("Button-Manager", self._open_manager)

        nav_tb = self.addToolBar("Navigation")
        nav_tb.setMovable(False)

        # -- Eine Ebene zurück
        self.act_back = QAction("← Zurück", self)
        self.act_back.setShortcut(QKeySequence(Qt.Key_Backspace))
        self.act_back.setEnabled(False)                  # in Root deaktiviert
        self.act_back.triggered.connect(self._go_back)
        nav_tb.addAction(self.act_back)

        # -- Direkt zum Start
        self.act_home = QAction("⏭ Start", self)
        self.act_home.setShortcut(QKeySequence(Qt.Key_Home))
        self.act_home.triggered.connect(self._go_home)
        nav_tb.addAction(self.act_home)

    # ------------------------------------------------------------------
    #   Daten-Helfer
    # ------------------------------------------------------------------
    def _children_of(self, parent_id: str | None):
        """Liefert alle Buttons, deren *parent* gleich *parent_id* ist."""
        return [b for b in self.cfg["buttons"] if b["parent"] == parent_id]

    # ------------------------------------------------------------------
    #   Seiten neu aufbauen
    # ------------------------------------------------------------------
    def _rebuild_pages(self) -> None:
        """Leert den QStackedWidget und baut alle MENU-Seiten neu auf."""
        # Reset Navigation
        self.nav_stack = [None]

        # Vorhandene Widgets entsorgen
        while self.pages.count():
            w = self.pages.widget(0)
            self.pages.removeWidget(w)
            w.deleteLater()
        self.page_for_id.clear()

        # --- Helper ----------------------------------------------------
        def build_page(parent_id: str | None) -> QWidget:
            page  = QWidget()
            grid  = QGridLayout(page)
            self.page_for_id[parent_id] = page

            children = self._children_of(parent_id)
            # Sortiert: erst Buttons mit Position, dann Rest
            children.sort(key=lambda b: (
                b.get("position", {}).get("row", 99),
                b.get("position", {}).get("col", 99),
            ))

            for cfg_btn in children:
                # ---- Position ------------------------------------------------
                if "position" in cfg_btn:
                    r = cfg_btn["position"]["row"]
                    c = cfg_btn["position"]["col"]
                else:
                    idx = grid.count()
                    r, c = divmod(idx, GRID_COLS)

                # ---- Button anlegen ----------------------------------------
                btn = QPushButton(cfg_btn["id"])
                if (ico := cfg_btn.get("icon")):
                    icon = QIcon(ico)
                    btn.setIcon(icon)
                    sizes = icon.availableSizes()
                    btn.setIconSize(sizes[0] if sizes else QSize(64, 64))

                if cfg_btn.get("description"):
                    btn.setToolTip(cfg_btn["description"])

                btn.clicked.connect(lambda _, b=cfg_btn: self._on_click(b))
                grid.addWidget(btn, r, c)
            return page

        # Root + alle MENU-Seiten bauen *und* in den Stack hängen
        root_page = build_page(None)
        self.pages.addWidget(root_page)

        for cfg_btn in self.cfg["buttons"]:
            if cfg_btn["action"] == "MENU":
                menu_page = build_page(cfg_btn["id"])
                self.pages.addWidget(menu_page)

        # UI-State -------------------------------------------------------
        self.pages.setCurrentWidget(root_page)
        self.act_back.setEnabled(False)
        self._update_breadcrumb()

    # ------------------------------------------------------------------
    #   Klick-Handler
    # ------------------------------------------------------------------
    def _on_click(self, cfg: dict) -> None:
        act = cfg["action"]

        # -------- Navigation -------------------------------------------
        if act == "MENU":
            self.nav_stack.append(cfg["id"])
            self.pages.setCurrentWidget(self.page_for_id[cfg["id"]])
            self._update_breadcrumb()
            self.act_back.setEnabled(True)
            return

        # -------- Aktionen ausführen -----------------------------------
        if act == "SCRIPT":
            subprocess.Popen([sys.executable, cfg["payload"]])
        elif act == "FILE":
            subprocess.Popen(cfg["payload"], shell=True)
        elif act == "LINK":
            QDesktopServices.openUrl(QUrl(cfg["payload"]))
        elif act == "FOLDER":
            subprocess.Popen(f'explorer "{cfg["payload"]}"')

    # ------------------------------------------------------------------
    #   Toolbar-Slots
    # ------------------------------------------------------------------
    def _go_back(self) -> None:
        if len(self.nav_stack) <= 1:
            return  # schon Root
        self.nav_stack.pop()
        prev_id = self.nav_stack[-1]
        self.pages.setCurrentWidget(self.page_for_id[prev_id])
        self._update_breadcrumb()
        self.act_back.setEnabled(len(self.nav_stack) > 1)

    def _go_home(self) -> None:
        self.nav_stack = [None]
        self.pages.setCurrentWidget(self.page_for_id[None])
        self._update_breadcrumb()
        self.act_back.setEnabled(False)

    # ------------------------------------------------------------------
    def _update_breadcrumb(self) -> None:
        crumbs = ["Start"] + self.nav_stack[1:]
        self._breadcrumb.setText(" / ".join(crumbs))

    # ------------------------------------------------------------------
    #   Button-Manager
    # ------------------------------------------------------------------
    def _open_manager(self) -> None:
        dlg = ButtonManager(self.cfg, self.cfg_path, self)
        if dlg.exec():
            storage.save_config(self.cfg_path, self.cfg)
            self._rebuild_pages()
