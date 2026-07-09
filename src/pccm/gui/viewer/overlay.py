"""2D overlay drawn on top of the 3D viewer (text, axis, scale bar)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pccm.gui.viewer.o3d_widget import Open3DWidget


class Overlay:
    """A simple 2D overlay drawn on the QLabel above the Open3D blit.

    This is a placeholder — full overlay rendering (with HTML-styled
    text, axis indicators, scale bars) is implemented in a later pass.
    """

    def __init__(self, widget: "Open3DWidget") -> None:
        self._widget = widget
        self._text: str = ""

    def set_text(self, text: str) -> None:
        self._text = text
