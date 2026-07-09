"""Central algorithm registry.

All algorithms (core, plugins, MATLAB ports) register themselves here
so that the GUI and CLI can discover them by id or category.

This module must **not** import PySide6.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from pccm.algorithms.base import Algorithm

logger = logging.getLogger(__name__)


class AlgorithmRegistry:
    """Singleton-ish registry that maps algorithm ids to instances.

    Usage::

        registry = AlgorithmRegistry()
        registry.register(MyAlgorithm())
        alg = registry.get("filter.voxel")
        for cat, algs in registry.by_category().items():
            ...

    The GUI reads ``by_category()`` to build menus and dialogs.
    """

    def __init__(self) -> None:
        self._registry: dict[str, Algorithm] = {}
        self._categories: dict[str, list[Algorithm]] = defaultdict(list)

    def register(self, algorithm: Algorithm) -> None:
        """Register an algorithm instance.

        Raises ``ValueError`` if the id is already registered with a
        different algorithm class (allows re-registering the same class
        for hot-reload).
        """
        alg_id = algorithm.id
        if not alg_id:
            raise ValueError("Algorithm must have a non-empty 'id'")
        existing = self._registry.get(alg_id)
        if existing is not None and type(existing) is not type(algorithm):
            logger.warning(
                "Replacing algorithm %r (%s) with %s",
                alg_id,
                type(existing).__name__,
                type(algorithm).__name__,
            )
        self._registry[alg_id] = algorithm
        if algorithm not in self._categories[algorithm.category]:
            self._categories[algorithm.category].append(algorithm)
        logger.debug("Registered algorithm: %s (%s)", alg_id, algorithm.name)

    def get(self, alg_id: str) -> Algorithm | None:
        """Look up an algorithm by id."""
        return self._registry.get(alg_id)

    def get_or_raise(self, alg_id: str) -> Algorithm:
        """Look up an algorithm by id, raising on missing."""
        alg = self._registry.get(alg_id)
        if alg is None:
            raise KeyError(f"No algorithm registered with id {alg_id!r}")
        return alg

    def by_category(self) -> dict[str, list[Algorithm]]:
        """Return ``{category: [Algorithm, ...]}`` sorted by category name."""
        return dict(sorted(self._categories.items()))

    def all_algorithms(self) -> list[Algorithm]:
        """Return all registered algorithms."""
        return list(self._registry.values())

    def unregister(self, alg_id: str) -> Algorithm | None:
        """Remove an algorithm from the registry (for plugin unload)."""
        alg = self._registry.pop(alg_id, None)
        if alg is not None:
            cat_list = self._categories.get(alg.category, [])
            if alg in cat_list:
                cat_list.remove(alg)
            logger.debug("Unregistered algorithm: %s", alg_id)
        return alg

    def __len__(self) -> int:
        return len(self._registry)

    def __contains__(self, alg_id: str) -> bool:
        return alg_id in self._registry


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

registry = AlgorithmRegistry()
