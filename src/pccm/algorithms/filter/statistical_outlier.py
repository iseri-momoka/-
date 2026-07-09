"""Statistical outlier removal (SOR).

For each point, compute the mean distance to its *k* nearest neighbours.
Points whose mean distance exceeds ``std_ratio × std`` of all distances
are classified as outliers and removed.
"""

from __future__ import annotations

import logging
from typing import Any

from pccm.algorithms.base import (
    AlgorithmBase,
    AlgorithmResult,
    ParamSpec,
    ParamType,
    RunContext,
)

logger = logging.getLogger(__name__)

PARAMS = (
    ParamSpec(
        name="nb_neighbors",
        label="Number of Neighbours",
        type=ParamType.INT,
        default=20,
        min=2,
        max=1000,
        help="Number of neighbours for mean-distance estimation.",
    ),
    ParamSpec(
        name="std_ratio",
        label="Std Ratio",
        type=ParamType.FLOAT,
        default=2.0,
        min=0.1,
        max=10.0,
        help="Points farther than mean + std_ratio × std are removed.",
    ),
)


class StatisticalOutlierRemoval(AlgorithmBase):
    """Statistical outlier removal using Open3D."""

    id = "filter.statistical_outlier"
    name = "Statistical Outlier Removal"
    category = "Filter"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        nb_neighbors: int = resolved["nb_neighbors"]
        std_ratio: float = resolved["std_ratio"]

        import open3d as o3d

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            pcd = entity.data
            if not isinstance(pcd, o3d.geometry.PointCloud):
                logger.warning("Skipping non-cloud entity %s", entity.name)
                continue
            original_count = len(pcd.points)
            clean, inlier_idx = pcd.remove_statistical_outlier(
                nb_neighbors, std_ratio
            )
            new_count = len(clean.points)
            ctx.report(1.0, f"SOR: {original_count} → {new_count} points")
            logger.info(
                "SOR %s: %d → %d (k=%d, std=%.2f)",
                entity.name,
                original_count,
                new_count,
                nb_neighbors,
                std_ratio,
            )
            from pccm.core.types import Entity, EntityKind

            out = Entity(
                name=f"{entity.name} (SOR)",
                kind=EntityKind.CLOUD,
                data=clean,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            diagnostics={"nb_neighbors": nb_neighbors, "std_ratio": std_ratio},
            display_name="Statistical Outlier Removal",
        )
