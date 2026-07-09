"""I/O format registry and reader/writer implementations.

Supported formats:
- PLY (via open3d)
- PCD (via open3d)
- LAS/LAZ (via laspy)
- OBJ (via open3d)
- E57 (via pye57)

Usage::

    from pccm.io import load_point_cloud, save_point_cloud
    pcd = load_point_cloud("scan.las")
    save_point_cloud("out.ply", pcd)
"""

from __future__ import annotations

import logging
from pathlib import Path

from pccm.core.errors import FileFormatError
from pccm.io.registry import FormatRegistry, registry

__all__ = ["FormatRegistry", "registry", "load_point_cloud", "save_point_cloud"]

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# High-level convenience API
# -------------------------------------------------------------------


def load_point_cloud(path: str | Path, **kwargs) -> "PointCloud":
    """Load a point cloud from any supported format.

    The format is determined from the file extension.

    Parameters
    ----------
    path : str or Path
        Path to the file.
    **kwargs
        Format-specific options passed to the reader.

    Returns
    -------
    open3d.geometry.PointCloud
        The loaded point cloud.

    Raises
    ------
    FileFormatError
        If the file extension is not supported or the file is corrupt.
    FileNotFoundError
        If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    reader = registry.get_reader(p.suffix)
    if reader is None:
        raise FileFormatError(
            f"Unsupported file format: {p.suffix!r}. "
            f"Supported: {', '.join(registry.supported_extensions())}"
        )
    logger.info("Loading %s with reader %r", p.name, type(reader).__name__)
    return reader.read(p, **kwargs)


def save_point_cloud(path: str | Path, cloud, **kwargs) -> None:
    """Save a point cloud to any supported format.

    Parameters
    ----------
    path : str or Path
        Destination path; extension determines format.
    cloud : open3d.geometry.PointCloud
        The point cloud to save.
    **kwargs
        Format-specific options passed to the writer.

    Raises
    ------
    FileFormatError
        If the file extension is not supported.
    """
    p = Path(path)
    writer = registry.get_writer(p.suffix)
    if writer is None:
        raise FileFormatError(
            f"Unsupported output format: {p.suffix!r}. "
            f"Supported: {', '.join(registry.supported_extensions())}"
        )
    logger.info("Saving %s with writer %r", p.name, type(writer).__name__)
    writer.write(p, cloud, **kwargs)
