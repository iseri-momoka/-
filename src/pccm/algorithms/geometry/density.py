"""Local point density estimation.

For each point, estimates the local density as the number of neighbours
within a given radius divided by the spherical volume.
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
    ),
)


class DensityEstimation(AlgorithmBase):
    """Density estimation using radius search."""

    id = "geometry.density"
    name = "Density Estimation"
    category = "Geometry"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        radius: float = resolved["search_radius"]

        import numpy as np

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind, ScalarField

        volume = (4.0 / 3.0) * np.pi * radius**3

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            pcd = entity.data
            if not isinstance(pcd, o3d.geometry.PointCloud):
                continue
            tree = o3d.geometry.KDTreeFlann(pcd)
            points = np.asarray(pcd.points)
            densities = np.zeros(len(points))
            for i in range(len(points)):
                [_, idx, _] = tree.search_radius_vector_3d(points[i], radius)
                densities[i] = len(idx) / volume
            sf = ScalarField(name="density", values=densities)
            ctx.report(1.0, f"Density computed for {len(points)} points")
            out = Entity(
                name=f"{entity.name} (density)",
                kind=EntityKind.CLOUD,
                data=pcd,
                scalar_field=sf,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            diagnostics={"radius": radius},
            display_name="Density Estimation",
        )
