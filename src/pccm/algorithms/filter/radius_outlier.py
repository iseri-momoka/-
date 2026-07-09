"""Radius-based outlier removal (ROR).

For each point, count neighbours within a fixed radius.  Points with fewer
than ``min_points`` neighbours are classified as outliers.
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
        name="nb_points",
        label="Min Points in Radius",
        type=ParamType.INT,
        default=10,
        min=1,
        max=10000,
        help="Minimum number of points within radius to keep a point.",
    ),
    ParamSpec(
        name="radius",
        label="Search Radius",
        type=ParamType.FLOAT,
        default=0.1,
        min=0.001,
        max=100.0,
        help="Radius around each point to search for neighbours.",
    ),
)


class RadiusOutlierRemoval(AlgorithmBase):
    """Radius outlier removal using Open3D."""

    id = "filter.radius_outlier"
    name = "Radius Outlier Removal"
    category = "Filter"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        nb_points: int = resolved["nb_points"]
        radius: float = resolved["radius"]

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
            clean, inlier_idx = pcd.remove_radius_outlier(nb_points, radius)
            new_count = len(clean.points)
            ctx.report(1.0, f"ROR: {original_count} → {new_count} points")
            logger.info(
                "ROR %s: %d → %d (min_pts=%d, r=%.4f)",
                entity.name,
                original_count,
                new_count,
                nb_points,
                radius,
            )
            from pccm.core.types import Entity, EntityKind

            out = Entity(
                name=f"{entity.name} (ROR)",
                kind=EntityKind.CLOUD,
                data=clean,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            diagnostics={"nb_points": nb_points, "radius": radius},
            display_name="Radius Outlier Removal",
        )
