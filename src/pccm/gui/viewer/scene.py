"""Document ↔ Open3DWidget scene synchronisation.

Subscribes to Document events and updates the viewer accordingly.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pccm.core.signals import (
    ENTITY_ADDED,
    ENTITY_REMOVED,
    ENTITY_REPLACED,
    SELECTION_CHANGED,
    VISIBILITY_CHANGED,
    bus,
)

if TYPE_CHECKING:
    from pccm.core.document import Document
    from pccm.gui.viewer.o3d_widget import Open3DWidget

logger = logging.getLogger(__name__)


class ViewerService:
    """High-level synchroniser between Document and the 3D widget.

    Listens to Document signals and mirrors changes to the Open3D
    widget.  Decides whether a change requires ``add_geometry``,
    ``update_geometry``, or a no-op.
    """

    def __init__(self, document: "Document", widget: "Open3DWidget") -> None:
        self._document = document
        self._widget = widget
        self._bus_connect()

    def _bus_connect(self) -> None:
        bus.connect(ENTITY_ADDED, lambda s, **kw: self._on_added(kw))
        bus.connect(ENTITY_REMOVED, lambda s, **kw: self._on_removed(kw))
        bus.connect(ENTITY_REPLACED, lambda s, **kw: self._on_replaced(kw))
        bus.connect(VISIBILITY_CHANGED, lambda s, **kw: self._on_visibility(kw))
        bus.connect(SELECTION_CHANGED, lambda s, **kw: self._on_selection(kw))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_added(self, kw: dict) -> None:
        entity_id = kw.get("entity_id")
        entity = self._document.get(entity_id)
        if entity is None or not entity.visible:
            return
        self._widget.add_geometry(entity_id, entity.data)

    def _on_removed(self, kw: dict) -> None:
        entity_id = kw.get("entity_id")
        entity = self._document.get(entity_id)
        if entity is not None:
            self._widget.remove_geometry(entity_id, entity.data)
        else:
            # Entity already deleted; nothing to remove from widget
            pass

    def _on_replaced(self, kw: dict) -> None:
        entity_id = kw.get("entity_id")
        entity = self._document.get(entity_id)
        if entity is not None:
            self._widget.update_geometry(entity.data)

    def _on_visibility(self, kw: dict) -> None:
        entity_id = kw.get("entity_id")
        visible = kw.get("visible", True)
        entity = self._document.get(entity_id)
        if entity is None:
            return
        if visible:
            self._widget.add_geometry(entity_id, entity.data)
        else:
            self._widget.remove_geometry(entity_id, entity.data)

    def _on_selection(self, kw: dict) -> None:
        # Selection highlighting is implemented as a colour override in a
        # later pass; placeholder keeps the signal in use.
        pass
