"""GUI tests — pytest-qt markers; run only on CI with xvfb."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.gui


def test_main_window_opens(qtbot):
    """Verify MainWindow can be constructed and shown."""
    pytest.importorskip("PySide6")
    from pccm.gui.main_window import MainWindow

    win = MainWindow()
    qtbot.addWidget(win.qmain)
    win.show()
    assert win.qmain.isVisible()
    assert win.qmain.windowTitle().startswith("PCCM")


def test_docks_present(qtbot):
    pytest.importorskip("PySide6")
    from pccm.gui.main_window import MainWindow

    win = MainWindow()
    qtbot.addWidget(win.qmain)
    win.show()
    for name in ("DB Tree", "Properties", "Histogram", "Python Console"):
        assert name in win.dock_widgets
        assert win.dock_widgets[name] is not None
