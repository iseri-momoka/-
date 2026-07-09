"""Geometry analysis algorithms.

Submodules:
- normals — normal vector estimation and orientation
- curvature — local curvature estimation via PCA
- density — local point density estimation
- plane_ransac — RANSAC plane fitting and extraction
- dbscan — DBSCAN clustering
- region_growing — region-growing segmentation
"""

from pccm.algorithms.registry import registry as _registry

from pccm.algorithms.geometry import (  # noqa: F401
    curvature,
    dbscan,
    density,
    normals,
    plane_ransac,
    region_growing,
)

__all__ = ["normals", "curvature", "density", "plane_ransac", "dbscan", "region_growing"]
