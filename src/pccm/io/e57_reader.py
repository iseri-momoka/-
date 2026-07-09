"""E57 file reader using pye57.

Reads ASTM E2808 E57 files (common in terrestrial laser scanners) into
an Open3D PointCloud.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from pccm.io.registry import Reader, registry

logger = logging.getLogger(__name__)


class E57Reader(Reader):
    """Read E57 files via pye57."""

    def read(self, path: Path, **kwargs: Any):
        import open3d as o3d
        import pye57

        e57 = pye57.E57(str(path))
        all_points = []
        for scan_idx in range(e57.scan_count):
            scan = e57.read_scan(scan_idx, scan_pose=False)
            for key in ("cartesianX", "cartesianY", "cartesianZ"):
                if key not in scan:
                    raise ValueError(f"E57 scan missing {key}")
            x = np.asarray(scan["cartesianX"])
            y = np.asarray(scan["cartesianY"])
            z = np.asarray(scan["cartesianZ"])
            valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
            all_points.append(np.column_stack([x[valid], y[valid], z[valid]]))
        if not all_points:
            raise ValueError(f"No valid points in E57 file: {path}")
        points = np.vstack(all_points).astype(np.float64)
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        logger.info(
            "Read E57 %s: %d points (from %d scans)",
            path.name,
            len(points),
            e57.scan_count,
        )
        return pcd


# Register
registry.register_reader(".e57", E57Reader())
