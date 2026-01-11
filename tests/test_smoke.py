from __future__ import annotations

from get_gphotos_data.core.paths import app_icon_bytes, qss_text
from get_gphotos_data.core.settings import Settings
from get_gphotos_data.core.ui_loader import ui_bytes
from get_gphotos_data.main_window import MainWindow


def test_constructs(qtbot):
    win = MainWindow(settings=Settings())
    qtbot.addWidget(win)
    assert win.windowTitle()


def test_assets_available():
    assert qss_text().strip()
    assert app_icon_bytes().startswith(b"\x89PNG")


def test_ui_files_available():
    assert ui_bytes("main_window.ui")
    assert ui_bytes("preferences_dialog.ui")
