"""OBJ file reader/writer using Open3D.

Handles simple Wavefront OBJ meshes and point clouds.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pccm.io.registry import Reader, Writer, registry

logger = logging.getLogger(__name__)


class OBJReader(Reader):
    """Read OBJ files via Open3D (as TriangleMesh)."""

    def read(self, path: Path, **kwargs: Any):
        import open3d as o3d

        mesh = o3d.io.read_triangle_mesh(str(path))
        if mesh is None or len(mesh.vertices) == 0:
            raise ValueError(f"Failed to read OBJ or file is empty: {path}")
        logger.info(
            "Read OBJ %s: %d vertices, %d triangles",
            path.name,
            len(mesh.vertices),
            len(mesh.triangles),
        )
        return mesh


class OBJWriter(Writer):
    """Write OBJ files via Open3D (TriangleMesh only)."""

    def write(self, path: Path, data: Any, **kwargs: Any) -> None:
        import open3d as o3d

        success = o3d.io.write_triangle_mesh(str(path), data, **kwargs)
        if not success:
            raise IOError(f"Failed to write OBJ: {path}")
        logger.info("Wrote OBJ %s", path.name)


# Register
registry.register_reader(".obj", OBJReader())
registry.register_writer(".obj", OBJWriter())
