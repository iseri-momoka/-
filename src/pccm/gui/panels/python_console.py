"""Python console panel — embeds a qtconsole bound to the ``pccm`` namespace.

Requires the optional ``qtconsole`` package.
"""

from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QPlainTextEdit, QVBoxLayout, QWidget


class PythonConsolePanel:
    """Dockable panel with a basic Python REPL placeholder.

    In production, this embeds ``qtconsole.rich_jupyter_widget`` bound
    to a ``pccm`` namespace.  The placeholder version ships with the
    default ``pccm.gui`` install so that ``pip install pccm`` does not
    require ``qtconsole``.
    """

    def __init__(self, document) -> None:
        self._document = document
        self.qdock = QDockWidget("Python Console")
        body = QWidget()
        self.qdock.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        self._editor = QPlainTextEdit(body)
        self._editor.setReadOnly(True)
        self._editor.setPlaceholderText(
            "Python console (qtconsole placeholder)\n"
            "Install qtconsole to enable live Python scripting."
        )
        layout.addWidget(self._editor)
