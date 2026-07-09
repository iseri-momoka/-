"""Properties panel — displays attributes of the currently selected entity.

Shows name, point count, bounds, scalar field stats, etc.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class PropertiesPanel:
    """Dockable panel showing the selected entity's properties."""

    def __init__(self, document) -> None:
        self._document = document
        self.qdock = QDockWidget("Properties")
        body = QWidget()
        self.qdock.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(4, 4, 4, 4)
        self._form = QFormLayout()
        layout.addLayout(self._form)

        self._lbl_name = QLabel("—")
        self._lbl_type = QLabel("—")
        self._lbl_points = QLabel("—")
        self._lbl_bounds = QLabel("—")

        self._form.addRow("Name", self._lbl_name)
        self._form.addRow("Type", self._lbl_type)
        self._form.addRow("Points", self._lbl_points)
        self._form.addRow("Bounds", self._lbl_bounds)
