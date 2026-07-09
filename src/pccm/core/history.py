"""Command pattern for undo / redo in the Document model.

Usage::

    from pccm.core.history import History
    from pccm.core.document import Document

    history = History(max_steps=100)
    history.execute(doc, AddEntityCommand(cloud, name="scan"))
    history.undo(doc)
    history.redo(doc)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING

from pccm.core.errors import UndoError

if TYPE_CHECKING:
    from pccm.core.document import Document


class Command(ABC):
    """Abstract command that knows how to execute and undo itself."""

    @abstractmethod
    def execute(self, doc: "Document") -> None:
        """Apply the command to *doc*."""

    @abstractmethod
    def undo(self, doc: "Document") -> None:
        """Reverse the effect of :meth:`execute` on *doc*."""

    @property
    def label(self) -> str:
        """Human-readable description shown in Edit → Undo <label>."""
        return self.__class__.__name__


class AddEntityCommand(Command):
    """Add an entity to the document."""

    def __init__(self, entity: "Entity", parent_id: str | None = None) -> None:
        from pccm.core.types import Entity

        if not isinstance(entity, Entity):
            raise TypeError(f"Expected Entity, got {type(entity).__name__}")
        self._entity = entity
        self._parent_id = parent_id
        self._added = False

    def execute(self, doc: "Document") -> None:
        doc._add_entity_direct(self._entity, self._parent_id)
        self._added = True

    def undo(self, doc: "Document") -> None:
        doc._remove_entity_direct(self._entity.id)
        self._added = False

    @property
    def label(self) -> str:
        return f"Add {self._entity.name}"


class DeleteEntityCommand(Command):
    """Remove one or more entities (with subtree) from the document."""

    def __init__(self, entity_ids: list[str]) -> None:
        self._ids = list(entity_ids)
        self._removed: dict[str, tuple["Entity", str | None]] = {}

    def execute(self, doc: "Document") -> None:
        for eid in self._ids:
            entity, parent_id = doc._pop_entity_direct(eid)
            self._removed[eid] = (entity, parent_id)

    def undo(self, doc: "Document") -> None:
        for eid, (entity, parent_id) in self._removed.items():
            doc._add_entity_direct(entity, parent_id)
        self._removed.clear()

    @property
    def label(self) -> str:
        return f"Delete {len(self._ids)} entity(ies)"


class ReplaceEntityCommand(Command):
    """Swap the data payload of an entity (e.g., after an algorithm)."""

    def __init__(self, entity_id: str, new_data: object, label_text: str = "") -> None:
        self._entity_id = entity_id
        self._new_data = new_data
        self._label_text = label_text
        self._old_data: object = None

    def execute(self, doc: "Document") -> None:
        entity = doc.get(self._entity_id)
        if entity is None:
            raise ValueError(f"Entity {self._entity_id!r} not found")
        self._old_data = entity.data
        entity.data = self._new_data

    def undo(self, doc: "Document") -> None:
        entity = doc.get(self._entity_id)
        if entity is None:
            return
        entity.data = self._old_data

    @property
    def label(self) -> str:
        return self._label_text or f"Replace {self._entity_id}"


class History:
    """A bounded undo / redo stack.

    Parameters
    ----------
    max_steps : int
        Maximum number of commands to retain.
    """

    def __init__(self, max_steps: int = 100) -> None:
        self._undo_stack: deque[Command] = deque(maxlen=max_steps)
        self._redo_stack: deque[Command] = deque(maxlen=max_steps)

    def execute(self, doc: "Document", command: Command) -> None:
        """Execute *command* and push it onto the undo stack."""
        command.execute(doc)
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def undo(self, doc: "Document") -> Command | None:
        """Undo the most recent command, if possible."""
        if not self._undo_stack:
            raise UndoError("Nothing to undo")
        cmd = self._undo_stack.pop()
        cmd.undo(doc)
        self._redo_stack.append(cmd)
        return cmd

    def redo(self, doc: "Document") -> Command | None:
        """Redo the most recently undone command, if possible."""
        if not self._redo_stack:
            raise UndoError("Nothing to redo")
        cmd = self._redo_stack.pop()
        cmd.execute(doc)
        self._undo_stack.append(cmd)
        return cmd

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_label(self) -> str | None:
        return self._undo_stack[-1].label if self._undo_stack else None

    @property
    def redo_label(self) -> str | None:
        return self._redo_stack[-1].label if self._redo_stack else None
