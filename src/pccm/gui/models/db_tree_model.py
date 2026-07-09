"""Entity tree model: QAbstractItemModel wrapper around Document."""

from __future__ import annotations

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


class EntityTreeModel(QAbstractItemModel):
    """Qt model that mirrors the Document's entity tree for QTreeView."""

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self._document = document

    # ------------------------------------------------------------------
    # Required overrides
    # ------------------------------------------------------------------

    def index(self, row, column, parent=QModelIndex()):
        # TODO: implement proper tree index based on entity hierarchy
        return self.createIndex(row, column, None)

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self._document.root_entities)

    def columnCount(self, parent=QModelIndex()):
        return 2  # Name, Type

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        entities = self._document.root_entities
        if index.row() >= len(entities):
            return None
        entity = entities[index.row()]
        if role == Qt.DisplayRole:
            return entity.name if index.column() == 0 else entity.kind.name
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return ["Name", "Type"][section]
        return None
