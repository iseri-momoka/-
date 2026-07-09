"""Spatial data structures.

Submodules:
- kdtree — Open3D KDTreeFlann wrapper for fast nearest-neighbour queries
- octree — Open3D Octree wrapper for hierarchical spatial indexing
"""

from pccm.spatial.kdtree import KDTree  # noqa: F401
from pccm.spatial.octree import Octree  # noqa: F401

__all__ = ["KDTree", "Octree"]
