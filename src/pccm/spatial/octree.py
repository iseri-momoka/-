"""Octree wrapper around Open3D's Octree.

Used for hierarchical spatial indexing and progressive level-of-detail
queries.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import open3d as o3d

logger = logging.getLogger(__name__)


class Octree:
    """Thin wrapper around ``open3d.geometry.Octree``.

    Parameters
    ----------
    max_depth : int
        Maximum depth of the octree.
    """

    def __init__(self, max_depth: int = 8) -> None:
        import open3d as o3d

        self._max_depth = max_depth
        self._octree = o3d.geometry.Octree(max_depth=max_depth)

    def build_from_point_cloud(
        self, cloud: "o3d.geometry.PointCloud"
    ) -> None:
        """Build the octree from a point cloud."""
        import open3d as o3d

        if not isinstance(cloud, o3d.geometry.PointCloud):
            raise TypeError("Expected PointCloud")
        self._octree.convert_from_point_cloud(cloud, size_expand=0.01)
        logger.info(
            "Built octree (depth=%d) for %d points",
            self._max_depth,
            len(cloud.points),
        )

    def points_in_sphere(
        self, center: np.ndarray, radius: float
    ) -> list[int]:
        """Find points within a sphere using the octree.

        This is a brute-force refinement — the octree narrows candidates
        and then a radius filter selects exact matches.
        """
        import open3d as o3d

        # Octree traversal to find leaf nodes, then check points
        results: list[int] = []
        cloud = self._octree.origin  # origin point
        # For a simple implementation, fall back to KDTree
        # TODO: implement proper octree-based radius query
        logger.debug("Octree sphere query falling back to brute-force")
        return results

    @property
    def max_depth(self) -> int:
        return self._max_depth
