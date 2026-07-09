"""The central document model for PCCM.

A ``Document`` holds an ordered collection of ``Entity`` objects (point
clouds, meshes, groups) plus a command history for undo/redo.  All
modifications to the document go through the history stack via commands.

The Document is intentionally **Qt-free** — GUI code subscribes to
blinker signals (see :mod:`pccm.core.signals`) to stay in sync.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import Any

from pccm.core.errors import DocumentError
from pccm.core.history import (
    AddEntityCommand,
    Command,
    DeleteEntityCommand,
    History,
    ReplaceEntityCommand,
)
from pccm.core.signals import (
    emit_entity_added,
    emit_entity_removed,
    emit_entity_renamed,
    emit_entity_replaced,
    emit_history_changed,
    emit_selection_changed,
)
from pccm.core.types import Entity, EntityKind

logger = logging.getLogger(__name__)


class Document:
    """The primary data container for all loaded entities.

    Parameters
    ----------
    history_steps : int
        Maximum undo stack depth (default 100).

    Attributes
    ----------
    history : History
        The undo/redo stack.
    """

    def __init__(self, history_steps: int = 100) -> None:
        self._entities: dict[str, Entity] = {}
        self._root_ids: list[str] = []  # ordered top-level entity ids
        self._selection: set[str] = set()
        self.history = History(max_steps=history_steps)

    # ------------------------------------------------------------------
    # Entity access
    # ------------------------------------------------------------------

    def get(self, entity_id: str) -> Entity | None:
        """Look up an entity by id (returns ``None`` if not found)."""
        return self._entities.get(entity_id)

    def get_or_raise(self, entity_id: str) -> Entity:
        """Look up an entity by id, raising on missing."""
        entity = self._entities.get(entity_id)
        if entity is None:
            raise DocumentError(f"Entity {entity_id!r} not found in document")
        return entity

    @property
    def entities(self) -> dict[str, Entity]:
        """Read-only view of id → Entity mapping."""
        return dict(self._entities)

    @property
    def root_entities(self) -> list[Entity]:
        """Top-level entities in insertion order."""
        return [self._entities[eid] for eid in self._root_ids if eid in self._entities]

    @property
    def selection(self) -> set[str]:
        """Currently selected entity ids."""
        return set(self._selection)

    @property
    def entity_count(self) -> int:
        return len(self._entities)

    # ------------------------------------------------------------------
    # Public mutation API (all go through History)
    # ------------------------------------------------------------------

    def add_cloud(
        self,
        pcd: Any,
        name: str | None = None,
        parent_id: str | None = None,
    ) -> Entity:
        """Create an Entity wrapping a PointCloud and add it to the document.

        Parameters
        ----------
        pcd : open3d.geometry.PointCloud
            The point cloud geometry.
        name : str, optional
            Display name. Defaults to ``"Cloud <N>"``.
        parent_id : str, optional
            Group id to add as child; ``None`` adds to root.

        Returns
        -------
        Entity
            The newly created entity.
        """
        if name is None:
            name = f"Cloud {self.entity_count + 1}"
        entity = Entity(name=name, kind=EntityKind.CLOUD, data=pcd)
        self.history.execute(self, AddEntityCommand(entity, parent_id))
        return entity

    def add_mesh(
        self,
        mesh: Any,
        name: str | None = None,
        parent_id: str | None = None,
    ) -> Entity:
        """Create an Entity wrapping a TriangleMesh and add it to the document."""
        if name is None:
            name = f"Mesh {self.entity_count + 1}"
        entity = Entity(name=name, kind=EntityKind.MESH, data=mesh)
        self.history.execute(self, AddEntityCommand(entity, parent_id))
        return entity

    def add_entity(
        self,
        entity: Entity,
        parent_id: str | None = None,
    ) -> None:
        """Add an existing Entity (undo-able)."""
        self.history.execute(self, AddEntityCommand(entity, parent_id))

    def delete(self, entity_ids: Iterable[str]) -> None:
        """Remove entities by id (undo-able).

        Passing a group id removes all descendants.
        """
        ids = list(entity_ids)
        if not ids:
            return
        # Expand groups to include all descendants
        expanded = set()
        for eid in ids:
            self._expand_id(eid, expanded)
        self.history.execute(self, DeleteEntityCommand(list(expanded)))
        # Remove from selection
        self._selection -= expanded
        emit_selection_changed(list(self._selection))
        self._emit_history()

    def replace(self, entity_id: str, new_data: Any, label: str = "") -> None:
        """Swap the data payload of an entity (undo-able)."""
        self.history.execute(
            self, ReplaceEntityCommand(entity_id, new_data, label_text=label)
        )
        emit_entity_replaced(entity_id)
        self._emit_history()

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def set_selection(self, entity_ids: Iterable[str]) -> None:
        """Replace the current selection (undo-able)."""
        self._selection = set(entity_ids)
        emit_selection_changed(list(self._selection))

    def select(self, entity_id: str) -> None:
        """Add a single entity to the selection."""
        self._selection.add(entity_id)
        emit_selection_changed(list(self._selection))

    def deselect(self, entity_id: str) -> None:
        """Remove a single entity from the selection."""
        self._selection.discard(entity_id)
        emit_selection_changed(list(self._selection))

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def set_visible(self, entity_id: str, visible: bool) -> None:
        """Toggle entity visibility."""
        entity = self.get_or_raise(entity_id)
        entity.visible = visible
        from pccm.core.signals import emit_visibility_changed

        emit_visibility_changed(entity_id, visible)

    # ------------------------------------------------------------------
    # Undo / Redo wrappers
    # ------------------------------------------------------------------

    def undo(self) -> None:
        self.history.undo(self)
        self._emit_history()

    def redo(self) -> None:
        self.history.redo(self)
        self._emit_history()

    @property
    def can_undo(self) -> bool:
        return self.history.can_undo

    @property
    def can_redo(self) -> bool:
        return self.history.can_redo

    @property
    def undo_label(self) -> str | None:
        return self.history.undo_label

    @property
    def redo_label(self) -> str | None:
        return self.history.redo_label

    # ------------------------------------------------------------------
    # Persistence (stubs — implemented in M3)
    # ------------------------------------------------------------------

    def save_project(self, path: str) -> None:
        """Save the document to a ``.pccm`` project file (zarr/npz)."""
        raise NotImplementedError("Project save is planned for M3")

    def load_project(self, path: str) -> None:
        """Load a ``.pccm`` project file into this document."""
        raise NotImplementedError("Project load is planned for M3")

    # ------------------------------------------------------------------
    # Internal helpers (called by Commands, not by user code)
    # ------------------------------------------------------------------

    def _add_entity_direct(
        self, entity: Entity, parent_id: str | None = None
    ) -> None:
        """Low-level add without going through History (used by Commands)."""
        if entity.id in self._entities:
            raise DocumentError(
                f"Entity {entity.id!r} already exists in document"
            )
        self._entities[entity.id] = entity
        if parent_id is not None:
            parent = self.get_or_raise(parent_id)
            if parent.kind != EntityKind.GROUP:
                raise DocumentError(
                    f"Parent {parent_id!r} is not a group"
                )
            parent.data.append(entity)
            entity.parent = parent
        else:
            self._root_ids.append(entity.id)
        emit_entity_added(entity.id, parent_id)
        self._emit_history()

    def _remove_entity_direct(self, entity_id: str) -> tuple[Entity, str | None]:
        """Low-level remove without going through History."""
        entity = self._entities.pop(entity_id)
        # Detach from parent
        parent_id: str | None = None
        if entity.parent is not None:
            parent_id = entity.parent.id
            entity.parent.data.remove(entity)  # type: ignore[union-attr]
            entity.parent = None
        else:
            if entity_id in self._root_ids:
                self._root_ids.remove(entity_id)
        emit_entity_removed(entity_id, parent_id)
        self._emit_history()
        return entity, parent_id

    def _pop_entity_direct(self, entity_id: str) -> tuple[Entity, str | None]:
        """Pop an entity and return it with its parent id (for undo)."""
        return self._remove_entity_direct(entity_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _expand_id(self, entity_id: str, out: set[str]) -> None:
        """Recursively expand a group into all descendant ids."""
        entity = self.get(entity_id)
        if entity is None:
            return
        out.add(entity_id)
        if entity.kind == EntityKind.GROUP:
            for child in entity.children:
                self._expand_id(child.id, out)

    def _emit_history(self) -> None:
        emit_history_changed(self.can_undo, self.can_redo)
