"""Moving Least Squares (MLS) smoothing.

Smooths a point cloud by fitting a local polynomial surface to each
point's neighbourhood and projecting onto the fitted surface.
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
        name="search_radius",
        label="Search Radius",
        type=ParamType.FLOAT,
        default=0.05,
        min=0.001,
        max=100.0,
        help="Neighbourhood radius for local surface fitting.",
    ),
    ParamSpec(
        name="nb_neighbors",
        label="Max Neighbours",
        type=ParamType.INT,
        default=30,
        min=3,
        max=1000,
        help="Maximum number of neighbours used per point.",
    ),
)


class MLSSmoothing(AlgorithmBase):
    """Moving Least Squares smoothing using Open3D MLS."""

    id = "filter.smoothing_mls"
    name = "MLS Smoothing"
    category = "Filter"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        search_radius: float = resolved["search_radius"]
        nb_neighbors: int = resolved["nb_neighbors"]

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

            # Compute normals first (required by MLS)
            pcd.estimate_normals(
                o3d.geometry.KDTreeSearchParamHybrid(
                    radius=search_radius * 2, max_nn=nb_neighbors
                )
            )
            smoothed = pcd.compute_moving_least_squares_normals(
                search_radius=search_radius, max_nn=nb_neighbors
            )
            if smoothed is None:
                logger.error("MLS smoothing failed for %s", entity.name)
                continue
            ctx.report(1.0, f"MLS smoothed {len(pcd.points)} points")
            from pccm.core.types import Entity, EntityKind

            out = Entity(
                name=f"{entity.name} (MLS)",
                kind=EntityKind.CLOUD,
                data=smoothed,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            diagnostics={"search_radius": search_radius, "nb_neighbors": nb_neighbors},
            display_name="MLS Smoothing",
        )
