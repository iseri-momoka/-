"""Open3D → Qt bridge: embed Open3D's Visualizer in a PySide6 QWidget.

The ``O3DVisualizer`` provided by Open3D is *not* a ``QWidget`` and
cannot be placed in a Qt layout directly.  Instead, we use an offscreen
window, render each frame, and blit the pixel buffer to a ``QLabel``.

Mouse / wheel events are forwarded to the Open3D visualizer so orbit,
pan, and zoom work normally.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

logger = logging.getLogger(__name__)


class Open3DWidget(QWidget):
    """QWidget that renders an offscreen Open3D visualizer and blits each frame.

    Signals
    -------
    geometry_added(str)
    geometry_removed(str)
    """

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setMouseTracking(True)

        # Open3D offscreen window (not visible)
        import open3d as o3d

        self._vis = o3d.visualization.Visualizer()
        self._vis.create_window(
            window_name="pccm-offscreen",
            width=1280,
            height=720,
            visible=False,
        )

        # Qt label that receives the rendered image
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # Track geometry names for add/remove
        self._geometry_names: set[str] = set()

        # Timer driving the render loop (~60 fps)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(16)

    # ------------------------------------------------------------------
    # Show / hide
    # ------------------------------------------------------------------

    def showEvent(self, e) -> None:  # noqa: N802
        self._timer.start()
        super().showEvent(e)

    def hideEvent(self, e) -> None:  # noqa: N802
        self._timer.stop()
        super().hideEvent(e)

    # ------------------------------------------------------------------
    # Render loop
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """Poll Open3D events, update renderer, blit to QLabel."""
        self._vis.poll_events()
        self._vis.update_renderer()
        try:
            buf = self._vis.capture_screen_float_buffer(do_render=True)
        except Exception:
            return
        arr = (np.asarray(buf) * 255).clip(0, 255).astype(np.uint8)
        h, w, _ = arr.shape
        bytes_per_line = 3 * w
        qimg = QImage(arr.data, w, h, bytes_per_line, QImage.Format_RGB888)
        qimg = qimg.rgbSwapped()
        pix = QPixmap.fromImage(qimg).scaled(
            self._label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._label.setPixmap(pix)

    # ------------------------------------------------------------------
    # Mouse / wheel forwarding
    # ------------------------------------------------------------------

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self._forward_mouse(e, "down")

    def mouseMoveEvent(self, e) -> None:  # noqa: N802
        self._forward_mouse(e, "move")

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        self._forward_mouse(e, "up")

    def wheelEvent(self, e) -> None:  # noqa: N802
        delta = e.angleDelta().y() / 120.0
        self._vis.get_view_control().zoom(delta)

    def _forward_mouse(self, e, kind: str) -> None:
        x = e.position().x()
        y = e.position().y()
        button = {
            Qt.MouseButton.LeftButton: "left",
            Qt.MouseButton.MiddleButton: "middle",
            Qt.MouseButton.RightButton: "right",
        }.get(e.button(), "left")
        if kind == "down":
            self._vis.get_view_control().rotate(x, y, x, y)
        elif kind == "move":
            self._vis.get_view_control().rotate(x, y, x, y)

    # ------------------------------------------------------------------
    # Geometry management
    # ------------------------------------------------------------------

    def add_geometry(self, name: str, geometry: Any) -> None:
        """Add an Open3D geometry (PointCloud or TriangleMesh) to the scene."""
        self._vis.add_geometry(geometry, reset_bounding_box=False)
        self._geometry_names.add(name)
        logger.debug("Added geometry: %s", name)

    def remove_geometry(self, name: str, geometry: Any) -> None:
        """Remove a geometry from the scene."""
        self._vis.remove_geometry(geometry)
        self._geometry_names.discard(name)
        logger.debug("Removed geometry: %s", name)

    def update_geometry(self, geometry: Any) -> None:
        """Notify Open3D that a geometry's data changed in-place."""
        self._vis.update_geometry(geometry)

    def reset_view(self) -> None:
        """Reset the camera to fit all visible geometry."""
        self._vis.reset_view_point(True)

    def screenshot(self, path: str) -> None:
        """Save a screenshot of the current view."""
        self._vis.capture_screen_image(path, do_render=True)
        logger.info("Screenshot saved: %s", path)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, e) -> None:  # noqa: N802
        self._timer.stop()
        self._vis.destroy_window()
        self._vis.close()
        super().closeEvent(e)
