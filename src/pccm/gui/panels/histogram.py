"""Histogram panel — embedded matplotlib chart showing scalar-field distribution."""

from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget


class HistogramPanel:
    """Dockable panel that draws the scalar field histogram."""

    def __init__(self, document) -> None:
        self._document = document
        self.qdock = QDockWidget("Histogram")
        body = QWidget()
        self.qdock.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        # matplotlib FigureCanvasQTAgg goes here in a later pass
        self._placeholder = QWidget()
        layout.addWidget(self._placeholder)
