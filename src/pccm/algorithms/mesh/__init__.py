"""Mesh reconstruction and editing algorithms.

Submodules:
- poisson — Poisson surface reconstruction
- decimate — quadric edge collapse decimation
- hole_fill — automatic hole filling
"""

from pccm.algorithms.registry import registry as _registry

from pccm.algorithms.mesh import (  # noqa: F401
    decimate,
    hole_fill,
    poisson,
)

__all__ = ["poisson", "decimate", "hole_fill"]
