"""Normal vector estimation.

Estimates per-point normals using PCA on the *k* nearest neighbours, then
optionally orients them consistently towards a reference direction.
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
        default=0.1,
        min=0.001,
        max=100.0,
        help="Radius for neighbourhood search during normal estimation.",
    ),
    ParamSpec(
        name="max_nn",
        label="Max Neighbours",
        type=ParamType.INT,
        default=30,
        min=3,
        max=500,
        help="Maximum number of neighbours per point.",
    ),
    ParamSpec(
        name="orient_up",
        label="Orient Upward",
        type=ParamType.BOOL,
        default=True,
        help="Orient normals consistently towards +Z.",
    ),
)


class NormalEstimation(AlgorithmBase):
    """Normal estimation using Open3D."""

    id = "geometry.normals"
    name = "Normal Estimation"
    category = "Geometry"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        radius: float = resolved["search_radius"]
        max_nn: int = resolved["max_nn"]
        orient_up: bool = resolved["orient_up"]

        import open3d as o3d

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            pcd = entity.data
            if not isinstance(pcd, o3d.geometry.PointCloud):
                continue
            pcd.estimate_normals(
                o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=max_nn)
            )
            if orient_up:
                pcd.orient_normals_consistent_tangent_plane(k=max_nn)
            ctx.report(1.0, f"Estimated normals for {len(pcd.points)} points")
            from pccm.core.types import Entity, EntityKind

            out = Entity(
                name=f"{entity.name} (normals)",
                kind=EntityKind.CLOUD,
                data=pcd,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            diagnostics={"radius": radius, "max_nn": max_nn},
            display_name="Normal Estimation",
        )
