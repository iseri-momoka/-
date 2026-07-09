"""Algorithm package: point cloud processing algorithms.

All submodules import Open3D lazily inside ``run()`` so that ``import
pccm.algorithms`` does not require a working Open3D install (useful for
linting, type checking, and headless unit tests).
"""

from pccm.algorithms.base import (
    Algorithm,
    AlgorithmBase,
    AlgorithmResult,
    ParamSpec,
    ParamType,
    RunContext,
)
from pccm.algorithms.registry import AlgorithmRegistry, registry

# Importing submodules causes them to self-register with the registry.
from pccm.algorithms import (  # noqa: F401
    distance,
    filter,
    geometry,
    mesh,
    registration,
    scalar_field,
)

__all__ = [
    "Algorithm",
    "AlgorithmBase",
    "AlgorithmResult",
    "ParamSpec",
    "ParamType",
    "RunContext",
    "AlgorithmRegistry",
    "registry",
]
