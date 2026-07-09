"""Cropping tools: axis-aligned bounding box and oriented bounding box."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import open3d as o3d

from pccm.core.types import Entity, EntityKind

logger = logging.getLogger(__name__)


class CropTool:
    """Crop a point cloud or mesh to a bounding box."""

    @staticmethod
    def crop_aabb(
        cloud: "o3d.geometry.PointCloud",
        min_bound: tuple[float, float, float],
        max_bound: tuple[float, float, float],
    ) -> Entity:
        """Crop to an axis-aligned bounding box."""
        import open3d as o3d

        bbox = o3d.geometry.AxisAlignedBoundingBox(
            min_bound=np.asarray(min_bound, dtype=np.float64),
            max_bound=np.asarray(max_bound, dtype=np.float64),
        )
        cropped = cloud.crop(bbox)
        logger.info("AABB crop: %d → %d points", len(cloud.points), len(cropped.points))
        return Entity(
            name="Cropped (AABB)",
            kind=EntityKind.CLOUD,
            data=cropped,
        )

    @staticmethod
    def crop_obb(
        cloud: "o3d.geometry.PointCloud",
        center: tuple[float, float, float],
        extent: tuple[float, float, float],
        rotation: np.ndarray | None = None,
    ) -> Entity:
        """Crop to an oriented bounding box."""
        import open3d as o3d

        obb = o3d.geometry.OrientedBoundingBox(
            center=np.asarray(center, dtype=np.float64),
            R=np.eye(3) if rotation is None else rotation,
            extent=np.asarray(extent, dtype=np.float64),
        )
        cropped = cloud.crop(obb)
        logger.info("OBB crop: %d → %d points", len(cloud.points), len(cropped.points))
        return Entity(
            name="Cropped (OBB)",
            kind=EntityKind.CLOUD,
            data=cropped,
        )
