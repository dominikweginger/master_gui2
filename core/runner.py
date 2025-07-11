#!/usr/bin/env python3
"""
ScriptRunner – führt ein externes Python-Skript non-blocking aus.

Features
--------
* läuft in QThreadPool → blockiert die GUI nicht
* schreibt Log in logs/<job_id>.log
* sendet Fortschritt + Nachrichten über core.dispatcher
* Abbruch-Unterstützung via dispatcher.job_abort_req
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QRunnable, Slot, QThreadPool

from core.dispatcher import dispatcher

# Globale Registry für Stop-Button (Dashboard) → Runner
RUNNERS: dict[str, "ScriptRunner"] = {}


class ScriptRunner(QRunnable):
    """
    Führt das gegebene Skript im Subprozess aus und leitet stdout/stderr Zeile für
    Zeile an das Dashboard weiter. Fortschritts-Parsing: erkennt “... 42%”
    am Zeilenende oder “[42%] ...”.
    """
    def __init__(self, job_id: str, script_path: Path):
        super().__init__()
        self.setAutoDelete(False)            # wichtig fürs Abbrechen
        self.job_id = job_id
        self.script_path = script_path
        self._proc: subprocess.Popen | None = None
        self._abort_flag = False
        self._log_path = Path("logs") / f"{job_id}.log"
        self._log_path.parent.mkdir(exist_ok=True, parents=True)

        # Abbruch-Signal annehmen
        dispatcher.job_abort_req.connect(self._on_abort_req)
        RUNNERS[job_id] = self               # registrieren

    # ------------------------------------------------------------------
    # Public API für das Dashboard (falls direkter Aufruf gewünscht)
    # ------------------------------------------------------------------
    def abort(self) -> None:
        """Bricht das laufende Skript ab (falls möglich)."""
        self._abort_flag = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()           # sanft
            time.sleep(0.2)
            if self._proc.poll() is None:
                self._proc.kill()            # hart

    # ------------------------------------------------------------------
    # Intern
    # ------------------------------------------------------------------
    @Slot(str)
    def _on_abort_req(self, job_id: str) -> None:
        if job_id == self.job_id:
            self.abort()

    # ---------------------------------------
    def run(self) -> None:                   # QRunnable entry-point
        dispatcher.job_progress.emit(self.job_id, 0, "Starte Skript …")
        start_ts = time.time()

        try:
            self._proc = subprocess.Popen(
                [sys.executable, str(self.script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True
            )

            with self._log_path.open("w", encoding="utf-8") as log_f:
                for line in self._proc.stdout:        # type: ignore[arg-type]
                    line = line.rstrip("\n")
                    log_f.write(line + "\n")

                    # Fortschritt ermitteln (optional)
                    progress = self._extract_percent(line)
                    dispatcher.job_progress.emit(
                        self.job_id,
                        progress if progress is not None else -1,
                        line
                    )

                    if self._abort_flag:
                        break

            rc = self._proc.wait()
            dur = time.time() - start_ts

            if self._abort_flag:
                dispatcher.job_aborted.emit(self.job_id)
                dispatcher.job_progress.emit(
                    self.job_id, 100,
                    f"⏹ Abgebrochen nach {dur:0.1f}s"
                )
            elif rc == 0:
                dispatcher.job_finished.emit(self.job_id)
                dispatcher.job_progress.emit(
                    self.job_id, 100,
                    f"✅ Fertig in {dur:0.1f}s"
                )
            else:
                dispatcher.job_error.emit(
                    self.job_id,
                    f"Exitcode {rc}"
                )
        except Exception as exc:
            dispatcher.job_error.emit(self.job_id, str(exc))

        finally:
            RUNNERS.pop(self.job_id, None)   # Clean-up

    # ----------------------------
    @staticmethod
    def _extract_percent(text: str) -> int | None:
        """
        Versucht am Zeilenende eine Prozentzahl (0-100) zu finden.
        """
        m = re.search(r"(\d{1,3})\s*%$", text) or re.search(r"\[(\d{1,3})%]", text)
        if m:
            try:
                val = int(m.group(1))
                return max(0, min(val, 100))
            except ValueError:
                return None
        return None


# --------------------------------------------------------------
# Hilfsfunktion – bequem starten ohne direkte Runner-Erzeugung
# --------------------------------------------------------------
def run_script_async(script_path: Path) -> str:
    """
    Erzeugt eine Runner-Instanz und schmeißt sie in den globalen Pool.
    Liefert die job_id zurück.
    """
    job_id = os.urandom(8).hex()
    runner = ScriptRunner(job_id, script_path)
    dispatcher.job_started.emit(job_id, script_path.name)
    QThreadPool.globalInstance().start(runner)
    return job_id
