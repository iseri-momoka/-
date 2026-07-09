"""DB tree panel — QTreeView reflecting the Document model.

Users select entities in the tree; selection changes emit
``SELECTION_CHANGED`` and are reflected in the viewer.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pccm.core.document import Document

from PySide6.QtWidgets import QDockWidget, QTreeView, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class DBTreePanel:
    """A dockable tree view mirroring the Document entity hierarchy."""

    def __init__(self, document: "Document") -> None:
        from pccm.gui.models.db_tree_model import EntityTreeModel

        self._document = document
        self.qdock = QDockWidget("DB Tree")
        body = QWidget()
        self.qdock.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        self._tree = QTreeView(body)
        self._model = EntityTreeModel(document)
        self._tree.setModel(self._model)
        layout.addWidget(self._tree)
