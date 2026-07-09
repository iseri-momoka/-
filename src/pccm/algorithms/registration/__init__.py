"""Point cloud registration algorithms.

Submodules:
- icp — Iterative Closest Point (point-to-point / point-to-plane)
- global_ransac — FPFH feature-based global registration via RANSAC
"""

from pccm.algorithms.registry import registry as _registry

from pccm.algorithms.registration import (  # noqa: F401
    global_ransac,
    icp,
)

__all__ = ["icp", "global_ransac"]
