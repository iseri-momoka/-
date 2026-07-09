"""Point cloud filtering algorithms.

Submodules:
- voxel — voxel grid downsampling
- statistical_outlier — statistical outlier removal (SOR)
- radius_outlier — radius-based outlier removal (ROR)
- smoothing — MLS moving-least-squares smoothing
"""

from pccm.algorithms.registry import registry as _registry

# Re-export so `from pccm.algorithms.filter import *` populates the registry.
from pccm.algorithms.filter import (  # noqa: F401
    radius_outlier,
    smoothing,
    statistical_outlier,
    voxel,
)

__all__ = ["voxel", "statistical_outlier", "radius_outlier", "smoothing"]
