#!/usr/bin/env python3
"""
Signal-Router für Job-Events.
Jede GUI-Komponente kann sich an die Signale hängen,
ohne direkte Referenzen aufeinander zu benötigen.
"""
from PySide6.QtCore import QObject, Signal


class Dispatcher(QObject):
    # job_id, skript-name
    job_started   = Signal(str, str)
    # job_id, fortschritt 0-100 (-1 = unbekannt), nachricht
    job_progress  = Signal(str, int, str)
    # job_id
    job_finished  = Signal(str)
    # job_id, fehlermeldung
    job_error     = Signal(str, str)
    # UI fordert Abbruch an → Runner reagiert
    job_abort_req = Signal(str)
    # Runner meldet “abgebrochen”
    job_aborted   = Signal(str)


# Singleton-Instanz
dispatcher: Dispatcher = Dispatcher()
