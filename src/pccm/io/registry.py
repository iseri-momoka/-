"""I/O format registry — maps file extensions to reader/writer classes.

Modules under ``pccm.io`` register their reader/writer classes at import
time so that ``pccm.io.load_point_cloud("scan.las")`` "just works".

This module must **not** import PySide6.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Abstract base classes
# -------------------------------------------------------------------


class Reader(ABC):
    """Base class for file format readers."""

    @abstractmethod
    def read(self, path: Path, **kwargs: Any) -> Any:
        """Read a file and return an Open3D PointCloud or TriangleMesh."""
        ...


class Writer(ABC):
    """Base class for file format writers."""

    @abstractmethod
    def write(self, path: Path, data: Any, **kwargs: Any) -> None:
        """Write *data* to *path*."""
        ...


# -------------------------------------------------------------------
# Format registry
# -------------------------------------------------------------------


class FormatRegistry:
    """Maps file extensions to reader/writer instances.

    Registration happens at module import time via ``register_reader``
    and ``register_writer``.  The singleton ``registry`` at module level
    is the single entry point.
    """

    def __init__(self) -> None:
        self._readers: dict[str, Reader] = {}
        self._writers: dict[str, Writer] = {}

    def register_reader(self, extension: str, reader: Reader) -> None:
        """Register a reader for a file extension (including the dot)."""
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        self._readers[ext] = reader
        logger.debug("Registered reader for %s: %s", ext, type(reader).__name__)

    def register_writer(self, extension: str, writer: Writer) -> None:
        """Register a writer for a file extension (including the dot)."""
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        self._writers[ext] = writer
        logger.debug("Registered writer for %s: %s", ext, type(writer).__name__)

    def get_reader(self, extension: str) -> Reader | None:
        return self._readers.get(extension.lower())

    def get_writer(self, extension: str) -> Writer | None:
        return self._writers.get(extension.lower())

    def supported_extensions(self) -> list[str]:
        """All extensions that have at least a reader."""
        return sorted(self._readers.keys())

    def writable_extensions(self) -> list[str]:
        """All extensions that have a writer."""
        return sorted(self._writers.keys())

    def __len__(self) -> int:
        return len(set(self._readers) | set(self._writers))


# Module-level singleton
registry = FormatRegistry()
