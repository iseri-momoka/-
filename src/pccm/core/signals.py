"""Application-wide signals (Qt-free event bus using blinker).

All inter-module communication goes through signals defined here,
never direct method calls across layers.

Usage::

    from pccm.core.signals import bus

    def on_entity_added(sender, entity_id):
        ...

    bus.connect("entity_added", on_entity_added)
    bus.send("entity_added", entity_id="abc123")
"""

from __future__ import annotations

import blinker

# -----------------------------------------------------------------------
# Namespace — one global bus shared across all layers (except PySide6).
# -----------------------------------------------------------------------

bus = blinker.Namespace()

# -----------------------------------------------------------------------
# Pre-defined signal names.
# -----------------------------------------------------------------------

# Document-level signals
ENTITY_ADDED: str = "entity_added"
ENTITY_REMOVED: str = "entity_removed"
ENTITY_REPLACED: str = "entity_replaced"
ENTITY_RENAMED: str = "entity_renamed"

# Selection
SELECTION_CHANGED: str = "selection_changed"

# Visibility / display
VISIBILITY_CHANGED: str = "visibility_changed"
COLOR_CHANGED: str = "color_changed"
SCALAR_FIELD_CHANGED: str = "scalar_field_changed"

# History
HISTORY_CHANGED: str = "history_changed"  # undo/redo state changed

# Plugins
PLUGIN_LOADED: str = "plugin_loaded"
PLUGIN_ERROR: str = "plugin_error"


# -----------------------------------------------------------------------
# Sender helpers (Document calls these after state changes).
# -----------------------------------------------------------------------

def emit_entity_added(entity_id: str, parent_id: str | None = None) -> None:
    """Emit after a new entity is added to the Document."""
    bus.send(ENTITY_ADDED, entity_id=entity_id, parent_id=parent_id)


def emit_entity_removed(entity_id: str, parent_id: str | None = None) -> None:
    """Emit after an entity is removed from the Document."""
    bus.send(ENTITY_REMOVED, entity_id=entity_id, parent_id=parent_id)


def emit_entity_replaced(entity_id: str) -> None:
    """Emit after an entity's data has been swapped (algorithm output)."""
    bus.send(ENTITY_REPLACED, entity_id=entity_id)


def emit_entity_renamed(entity_id: str, old_name: str, new_name: str) -> None:
    """Emit after an entity is renamed."""
    bus.send(
        ENTITY_RENAMED, entity_id=entity_id, old_name=old_name, new_name=new_name
    )


def emit_selection_changed(selected_ids: list[str]) -> None:
    """Emit when the user changes the selection in the DB tree or viewer."""
    bus.send(SELECTION_CHANGED, selected_ids=selected_ids)


def emit_visibility_changed(entity_id: str, visible: bool) -> None:
    """Emit when an entity's visibility is toggled."""
    bus.send(VISIBILITY_CHANGED, entity_id=entity_id, visible=visible)


def emit_history_changed(can_undo: bool, can_redo: bool) -> None:
    """Emit when the undo/redo stack changes (for UI button state)."""
    bus.send(HISTORY_CHANGED, can_undo=can_undo, can_redo=can_redo)
