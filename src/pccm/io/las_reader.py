"""LAS/LAZ file reader using laspy.

Reads LAS 1.0–1.4 and LAZ (compressed) files into an Open3D
PointCloud while preserving point attributes as annotations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from pccm.io.registry import Reader, registry

logger = logging.getLogger(__name__)


class LASReader(Reader):
    """Read LAS/LAZ files via laspy and convert to Open3D PointCloud."""

    def read(self, path: Path, **kwargs: Any):
        import laspy
        import open3d as o3d

        las = laspy.read(str(path))
        points = np.vstack(
            (las.x, las.y, las.z)
        ).T.astype(np.float64)
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        # Preserve RGB if present
        if hasattr(las, "red") and hasattr(las, "green") and hasattr(las, "blue"):
            rgb = np.vstack((las.red, las.green, las.blue)).T.astype(np.float64)
            # LAS stores RGB in 16-bit; normalize to [0,1]
            if rgb.max() > 1.0:
                rgb /= 65535.0
            pcd.colors = o3d.utility.Vector3dVector(rgb[:, :3])

        # Preserve classification as annotation
        if hasattr(las, "classification"):
            classification = np.array(las.classification)
        else:
            classification = None

        pcd.annotations = {"classification": classification}  # type: ignore[attr-defined]
        logger.info(
            "Read LAS/LAZ %s: %d points", path.name, len(points)
        )
        return pcd


# Register
registry.register_reader(".las", LASReader())
registry.register_reader(".laz", LASReader())
