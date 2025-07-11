import sys, time
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from core.storage import load_config
from ui.master_window import MasterWindow

@pytest.mark.qt
def test_app_startup(qtbot: QtBot):
    app = QApplication.instance() or QApplication(sys.argv)
    cfg = load_config(Path("config.json"))

    # <<< ICONS IGNORIEREN >>>
    for btn in cfg["buttons"]:
        btn["icon"] = ""

    mw = MasterWindow(cfg)
    qtbot.addWidget(mw)
    mw.show()
    qtbot.wait(1000)
