"""PCD file reader/writer using Open3D.

Handles ASCII and binary PCD formats.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pccm.io.registry import Reader, Writer, registry

logger = logging.getLogger(__name__)


class PCDReader(Reader):
    """Read PCD files via Open3D."""

    def read(self, path: Path, **kwargs: Any):
        import open3d as o3d

        data = o3d.io.read_point_cloud(str(path))
        if data is None or len(data.points) == 0:
            raise ValueError(f"Failed to read PCD or file is empty: {path}")
        logger.info("Read PCD %s: %d points", path.name, len(data.points))
        return data


class PCDWriter(Writer):
    """Write PCD files via Open3D."""

    def write(self, path: Path, data: Any, **kwargs: Any) -> None:
        import open3d as o3d

        success = o3d.io.write_point_cloud(str(path), data, **kwargs)
        if not success:
            raise IOError(f"Failed to write PCD: {path}")
        logger.info("Wrote PCD %s", path.name)


# Register
registry.register_reader(".pcd", PCDReader())
registry.register_writer(".pcd", PCDWriter())
