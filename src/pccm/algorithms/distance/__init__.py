"""Distance computation algorithms.

Submodules:
- cloud_to_cloud — point-to-point distance between two clouds
- cloud_to_mesh — point-to-mesh distance
- m3c2 — M3C2-style signed distance with scale and confidence
"""

from pccm.algorithms.registry import registry as _registry

from pccm.algorithms.distance import (  # noqa: F401
    cloud_to_cloud,
    cloud_to_mesh,
    m3c2,
)

__all__ = ["cloud_to_cloud", "cloud_to_mesh", "m3c2"]
