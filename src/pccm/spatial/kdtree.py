"""KDTree wrapper around Open3D's KDTreeFlann.

Provides a friendlier Python API and a numpy-first interface.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import open3d as o3d

logger = logging.getLogger(__name__)


class KDTree:
    """Thin wrapper around ``open3d.geometry.KDTreeFlann``.

    Parameters
    ----------
    cloud : open3d.geometry.PointCloud
        The cloud to build the tree over.
    """

    def __init__(self, cloud: "o3d.geometry.PointCloud") -> None:
        import open3d as o3d

        if not isinstance(cloud, o3d.geometry.PointCloud):
            raise TypeError(
                f"KDTree requires PointCloud, got {type(cloud).__name__}"
            )
        self._cloud = cloud
        self._tree = o3d.geometry.KDTreeFlann(cloud)

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def search_knn(self, point: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        """Find *k* nearest neighbours of *point*.

        Returns ``(distances, indices)`` as numpy arrays.
        """
        [_, idx, dist2] = self._tree.search_knn_vector_3d(point, k)
        return np.asarray(dist2, dtype=np.float64) ** 0.5, np.asarray(idx, dtype=np.int64)

    def search_radius(
        self, point: np.ndarray, radius: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """Find all neighbours of *point* within *radius*."""
        [_, idx, dist2] = self._tree.search_radius_vector_3d(point, radius)
        return np.asarray(dist2, dtype=np.float64) ** 0.5, np.asarray(idx, dtype=np.int64)

    def search_hybrid(
        self, point: np.ndarray, radius: float, max_nn: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Hybrid search: up to *max_nn* neighbours within *radius*."""
        [_, idx, dist2] = self._tree.search_hybrid_vector_3d(point, radius, max_nn)
        return np.asarray(dist2, dtype=np.float64) ** 0.5, np.asarray(idx, dtype=np.int64)

    def search_all_knn(self, k: int) -> np.ndarray:
        """Compute k-NN for all points in the cloud.

        Returns an ``(N, k)`` int array of indices.
        """
        import open3d as o3d

        points = np.asarray(self._cloud.points)
        n = len(points)
        result = np.zeros((n, k), dtype=np.int64)
        for i in range(n):
            [_, idx, _] = self._tree.search_knn_vector_3d(points[i], k)
            result[i, : len(idx)] = idx
        return result
