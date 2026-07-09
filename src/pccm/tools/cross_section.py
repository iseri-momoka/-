"""Cross-section tool: extract points within a slab of thickness *t* around a plane."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import open3d as o3d

from pccm.core.types import Entity, EntityKind

logger = logging.getLogger(__name__)


class CrossSectionTool:
    """Extract a cross-section of a point cloud.

    A plane is defined by a point and a normal; points within ``thickness``
    of the plane are selected.
    """

    @staticmethod
    def extract(
        cloud: "o3d.geometry.PointCloud",
        plane_point: tuple[float, float, float],
        plane_normal: tuple[float, float, float],
        thickness: float,
    ) -> Entity:
        """Return a new entity containing points within *thickness* of the plane.

        Parameters
        ----------
        cloud : open3d.geometry.PointCloud
        plane_point : tuple
            A point on the plane.
        plane_normal : tuple
            Plane normal vector (does not need to be unit length).
        thickness : float
            Half-thickness of the slab.
        """
        points = np.asarray(cloud.points)
        p0 = np.asarray(plane_point, dtype=np.float64)
        n = np.asarray(plane_normal, dtype=np.float64)
        n_norm = np.linalg.norm(n)
        if n_norm == 0:
            raise ValueError("Plane normal must be non-zero")
        n_unit = n / n_norm
        # Signed distance from each point to the plane
        signed_dist = (points - p0) @ n_unit
        mask = np.abs(signed_dist) <= thickness
        indices = np.where(mask)[0].tolist()
        subset = cloud.select_by_index(indices)
        logger.info(
            "Cross-section: %d / %d points (thickness=%.4f)",
            len(indices),
            len(points),
            thickness,
        )
        return Entity(
            name=f"Cross-section (n={tuple(n_unit.round(3))})",
            kind=EntityKind.CLOUD,
            data=subset,
        )
