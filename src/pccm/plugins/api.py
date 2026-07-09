"""Plugin public API — the only symbols plugin authors should import.

All plugin modules import from this file instead of reaching into
``pccm.algorithms`` or ``pccm.core`` directly.  This keeps the plugin
contract stable even when internal implementations change.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import numpy  # noqa: F401 — re-exported for plugins

# Re-export algorithm protocol types
from pccm.algorithms.base import (  # noqa: F401
    Algorithm,
    AlgorithmBase,
    AlgorithmResult,
    ParamSpec,
    ParamType,
    RunContext,
)
from pccm.core.types import ScalarField, Entity  # noqa: F401

# Re-export open3d under a controlled namespace
try:
    import open3d as o3d  # noqa: F401
except ImportError:
    o3d = None  # type: ignore[assignment]

try:
    import scipy  # noqa: F401
except ImportError:
    scipy = None  # type: ignore[assignment]

try:
    import sklearn  # noqa: F401
except ImportError:
    sklearn = None  # type: ignore[assignment]

try:
    import matplotlib  # noqa: F401
except ImportError:
    matplotlib = None  # type: ignore[assignment]


def register(algorithm: Algorithm) -> None:
    """Register an algorithm instance with the global registry.

    Called once at import time in each plugin module::

        from pccm.plugins.api import register
        register(MyAlgorithm())
    """
    from pccm.algorithms.registry import registry as _registry

    _registry.register(algorithm)


def register_all(*algorithms: Algorithm) -> None:
    """Convenience: register multiple algorithms in one call."""
    from pccm.algorithms.registry import registry as _registry

    for alg in algorithms:
        _registry.register(alg)


__all__ = [
    "Algorithm",
    "AlgorithmBase",
    "AlgorithmResult",
    "ParamSpec",
    "ParamType",
    "RunContext",
    "ScalarField",
    "Entity",
    "numpy",
    "o3d",
    "scipy",
    "sklearn",
    "matplotlib",
    "register",
    "register_all",
]
