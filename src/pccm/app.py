"""QApplication bootstrap and main event-loop entry.

This module is the *only* place that creates the ``QApplication`` instance.
All other GUI code receives it via ``QApplication.instance()``.
"""

from __future__ import annotations

import logging
import sys
from typing import Sequence

from pccm._version import APP_NAME, __version__

logger = logging.getLogger(__name__)


def create_app(argv: Sequence[str] | None = None) -> "QtWidgets.QApplication":
    """Create and configure the Qt application object."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    if argv is None:
        argv = sys.argv

    app = QApplication(list(argv))
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("PCCM")

    # High-DPI scaling (Qt 6 default; explicit for clarity)
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Apply stylesheet if present
    _apply_stylesheet(app)

    logger.info("%s v%s started", APP_NAME, __version__)
    return app


def run(app: "QtWidgets.QApplication") -> int:
    """Show the main window and start the event loop."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from pccm.gui.main_window import MainWindow

    window = MainWindow()
    window.show()

    # Allow deferred initialisation (plugin loading, recent files, etc.)
    QTimer.singleShot(0, lambda: _on_idle(window))

    return app.exec()


# ------------------------------------------------------------------ internal

def _apply_stylesheet(app: "QtWidgets.QApplication") -> None:
    """Apply bundled QSS stylesheet, if it exists."""
    from importlib import resources

    from PySide6.QtGui import QFont

    # Set a sensible default font
    font = QFont("Segoe UI", 9)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # Load styles/qss/default.qss if bundled
    try:
        qss_dir = resources.files("pccm.gui.resources.styles")
        qss_file = qss_dir / "default.qss"
        if qss_file.is_file():
            app.setStyleSheet(qss_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, ModuleNotFoundError):
        pass  # Styles are optional


def _on_idle(window: "MainWindow") -> None:
    """Run once after the event loop is live (plugin init, recent files, etc.)."""
    logger.debug("Idle callback: post-show initialisation complete")
