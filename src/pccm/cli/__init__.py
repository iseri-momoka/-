"""CLI interface for CloudCompare ↔ Python algorithm bridge.

This module provides a command-line entry point that CloudCompare's
``ccCommandLineInterface`` can invoke via pipes or subprocess calls.
It reads input point cloud files, dispatches to Python algorithms
through the :class:`~pccm.algorithms.registry.AlgorithmRegistry`,
and serializes results for CloudCompare to consume.

Usage::

    # List all available algorithms
    python -m pccm.cli list

    # Run an algorithm
    python -m pccm.cli run filter.voxel --input scan.ply --output result.ply \\
        --voxel_size 0.05

    # Run with JSON params
    python -m pccm.cli run filter.voxel --input scan.ply --output result.ply \\
        --params '{"voxel_size": 0.05}'

Architecture Constraint: This module must **not** import PySide6 or
``pccm.gui``.  It operates entirely in headless mode.
"""

from pccm.cli.dispatcher import dispatch, main
from pccm.cli.formatter import format_result

__all__ = ["dispatch", "main", "format_result"]
