"""Unified writer API.

Currently delegates to per-format writers registered in the
:class:`FormatRegistry`.  See individual reader modules (ply_reader,
etc.) for the actual writer implementations.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pccm.core.errors import FileFormatError
from pccm.io.registry import registry

logger = logging.getLogger(__name__)


def save(path: str | Path, data, **kwargs) -> None:
    """Save data to *path* using the appropriate format writer.

    The file extension determines the format.

    Parameters
    ----------
    path : str or Path
        Destination file path.
    data :
        Open3D PointCloud or TriangleMesh.
    **kwargs
        Format-specific options forwarded to the writer.
    """
    p = Path(path)
    writer = registry.get_writer(p.suffix)
    if writer is None:
        raise FileFormatError(
            f"No writer registered for {p.suffix!r}. "
            f"Available write formats: {', '.join(registry.writable_extensions())}"
        )
    writer.write(p, data, **kwargs)
    logger.info("Saved %s (%s)", p.name, type(data).__name__)
