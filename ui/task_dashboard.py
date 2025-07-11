#!/usr/bin/env python3
"""
TaskDashboard – zeigt alle laufenden & erledigten Skripte.

* Tabelle oben: ID | Skript | Status | Laufzeit | Fortschritt | Stop
* QTextEdit unten: Live-Log des selektierten Jobs
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QProgressBar, QTextEdit
)

from core.dispatcher import dispatcher
from core.runner import RUNNERS


class TaskDashboard(QDialog):
    """Singleton-Fenster (non-modal) – blockiert das Hauptfenster NICHT."""

    COL_JOBID = 0
    COL_NAME = 1
    COL_STATUS = 2
    COL_RUNTIME = 3
    COL_PROGRESS = 4
    COL_STOP = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Task-Dashboard")
        self.resize(720, 480)
        self.setWindowFlag(Qt.Window)               # eigenes Fenster
        self._rows: Dict[str, int] = {}             # job_id → Zeilennummer
        self._starts: Dict[str, _dt.datetime] = {}

        # ------------------------- Widgets
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Job-ID", "Skript", "Status", "Laufzeit", "Fortschritt", ""]
        )
        self.table.setColumnHidden(self.COL_JOBID, True)     # nicht nötig
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnWidth(self.COL_STOP, 70)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))

        layout = QVBoxLayout(self)
        layout.addWidget(self.table, stretch=3)
        layout.addWidget(QLabel("Log-Ausgabe"), 0, Qt.AlignLeft)
        layout.addWidget(self.log_view, stretch=2)

        # ------------------------- Signale
        dispatcher.job_started.connect(self._on_job_started)
        dispatcher.job_progress.connect(self._on_job_progress)
        dispatcher.job_finished.connect(self._on_job_finished)
        dispatcher.job_aborted.connect(self._on_job_aborted)
        dispatcher.job_error.connect(self._on_job_error)

        self.table.itemSelectionChanged.connect(self._show_selected_log)

        # Timer → Laufzeitspalte tickt jede Sekunde
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_runtimes)
        self._timer.start(1_000)

    # ---------------------------------------------------------------------
    # Slot-Implementierungen
    # ---------------------------------------------------------------------
    def _on_job_started(self, job_id: str, name: str) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        self._rows[job_id] = row
        self._starts[job_id] = _dt.datetime.now()

        # ID
        self.table.setItem(row, self.COL_JOBID, QTableWidgetItem(job_id))
        # Skript-Name
        self.table.setItem(row, self.COL_NAME, QTableWidgetItem(name))
        # Status
        self.table.setItem(row, self.COL_STATUS, QTableWidgetItem("⏳ Läuft"))
        # Laufzeit
        self.table.setItem(row, self.COL_RUNTIME, QTableWidgetItem("0 s"))
        # Fortschritt
        pb = QProgressBar()
        pb.setRange(0, 100)
        pb.setValue(0)
        self.table.setCellWidget(row, self.COL_PROGRESS, pb)
        # Stop-Button
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(lambda _, jid=job_id: self._abort_job(jid))
        self.table.setCellWidget(row, self.COL_STOP, stop_btn)

    # --------------------------------
    def _on_job_progress(self, job_id: str, percent: int, msg: str) -> None:
        if job_id not in self._rows:
            return
        row = self._rows[job_id]
        # Fortschritt aktualisieren
        if percent >= 0:
            pb = self.table.cellWidget(row, self.COL_PROGRESS)
            if isinstance(pb, QProgressBar):
                pb.setValue(percent)
        # Log anhängen (falls Job selektiert)
        if self._current_job_id() == job_id:
            self.log_view.append(msg)

    # --------------------------------
    def _on_job_finished(self, job_id: str) -> None:
        self._set_status(job_id, "✅ Fertig")

    def _on_job_aborted(self, job_id: str) -> None:
        self._set_status(job_id, "⏹ Abgebrochen")

    def _on_job_error(self, job_id: str, err: str) -> None:
        self._set_status(job_id, f"❌ Fehler: {err}")

    # ---------------------------------------------------------------------
    # Helper
    # ---------------------------------------------------------------------
    def _set_status(self, job_id: str, text: str) -> None:
        if job_id in self._rows:
            self.table.item(self._rows[job_id], self.COL_STATUS).setText(text)

    def _abort_job(self, job_id: str) -> None:
        dispatcher.job_abort_req.emit(job_id)                # Runner hört zu

    def _update_runtimes(self) -> None:
        now = _dt.datetime.now()
        for job_id, start in self._starts.items():
            if job_id in self._rows:
                elapsed = now - start
                sec = int(elapsed.total_seconds())
                self.table.item(self._rows[job_id], self.COL_RUNTIME).setText(f"{sec}s")

    # --------------------------------
    def _current_job_id(self) -> str | None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            return self.table.item(rows[0].row(), self.COL_JOBID).text()
        return None

    def _show_selected_log(self) -> None:
        job_id = self._current_job_id()
        if not job_id:
            self.log_view.clear()
            return

        log_path = Path("logs") / f"{job_id}.log"
        if log_path.exists():
            self.log_view.setPlainText(log_path.read_text(encoding="utf-8"))
        else:
            self.log_view.setPlainText("(Noch keine Log-Ausgabe …)")
