"""Selection tools: rectangle and polygon (lasso) selection.

These return boolean masks over a point cloud's point array.  The GUI
layer uses them to highlight selected points and emit selection signals.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import open3d as o3d

logger = logging.getLogger(__name__)


class RectangleSelector:
    """Axis-aligned rectangle selection in screen space.

    The rectangle is defined in the viewer's pixel coordinates; converting
    those to world-space is done in the GUI layer (3D ray casting).
    This class holds the *results* of that conversion: a 2D bounding
    box in world coordinates.
    """

    def __init__(self, min_xy: np.ndarray, max_xy: np.ndarray) -> None:
        self.min_xy = np.asarray(min_xy, dtype=np.float64)
        self.max_xy = np.asarray(max_xy, dtype=np.float64)

    def select(self, cloud: "o3d.geometry.PointCloud") -> np.ndarray:
        """Return a boolean mask over cloud points inside the rectangle.

        The rectangle is treated as a vertical extrusion — any point whose
        X, Y fall inside is selected regardless of Z.
        """
        points = np.asarray(cloud.points)
        mask = (
            (points[:, 0] >= self.min_xy[0])
            & (points[:, 0] <= self.max_xy[0])
            & (points[:, 1] >= self.min_xy[1])
            & (points[:, 1] <= self.max_xy[1])
        )
        return mask


class PolygonSelector:
    """Arbitrary polygon (lasso) selection in XY plane."""

    def __init__(self, vertices_xy: list[tuple[float, float]]) -> None:
        if len(vertices_xy) < 3:
            raise ValueError("Polygon requires at least 3 vertices")
        self.vertices = np.asarray(vertices_xy, dtype=np.float64)
        try:
            from shapely.geometry import Polygon  # type: ignore[import-not-found]
        except ImportError:
            raise ImportError(
                "PolygonSelector requires shapely. Install with: pip install shapely"
            )
        self._poly = Polygon(self.vertices)

    def select(self, cloud: "o3d.geometry.PointCloud") -> np.ndarray:
        points = np.asarray(cloud.points)
        if len(points) == 0:
            return np.zeros(0, dtype=bool)
        from shapely.geometry import Point  # type: ignore[import-not-found]

        mask = np.zeros(len(points), dtype=bool)
        for i, p in enumerate(points[:, :2]):
            mask[i] = self._poly.contains(Point(p))
        return mask
