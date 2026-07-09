"""Scalar field computation, colorization, and histogram utilities.

Submodules:
- compute — derive a scalar field from a cloud (height, axis, distance)
- histogram — compute histogram bins for visualization
- colorize — apply a matplotlib colormap to per-point scalar values
"""

from pccm.algorithms.registry import registry as _registry

from pccm.algorithms.scalar_field import (  # noqa: F401
    colorize,
    compute,
    histogram,
)

__all__ = ["compute", "histogram", "colorize"]
