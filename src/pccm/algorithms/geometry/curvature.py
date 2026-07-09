"""Local curvature estimation via PCA.

For each point, performs PCA on its *k* nearest neighbours and derives
curvature from the eigenvalue spread: the ratio of the smallest eigenvalue
to the sum of all three eigenvalues.
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
    ParamSpec(
        name="max_nn",
        label="Max Neighbours",
        type=ParamType.INT,
        default=30,
        min=3,
        max=500,
    ),
)


class CurvatureEstimation(AlgorithmBase):
    """Curvature estimation using PCA on local neighbourhood."""

    id = "geometry.curvature"
    name = "Curvature Estimation"
    category = "Geometry"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        radius: float = resolved["search_radius"]
        max_nn: int = resolved["max_nn"]

        import numpy as np

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind, ScalarField

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            pcd = entity.data
            if not isinstance(pcd, o3d.geometry.PointCloud):
                continue
            points = np.asarray(pcd.points)
            tree = o3d.geometry.KDTreeFlann(pcd)
            curvatures = np.zeros(len(points))
            for i in range(len(points)):
                [_, idx, _] = tree.search_radius_vector_3d(points[i], radius)
                if len(idx) < 3:
                    continue
                neighbours = points[idx]
                cov = np.cov(neighbours.T)
                eigenvalues = np.linalg.eigvalsh(cov)
                total = eigenvalues.sum()
                if total > 0:
                    curvatures[i] = eigenvalues[0] / total  # smallest / total
            sf = ScalarField(name="curvature", values=curvatures)
            ctx.report(1.0, f"Curvature computed for {len(points)} points")
            from pccm.core.types import Entity as _E, EntityKind as _K

            out = Entity(
                name=f"{entity.name} (curvature)",
                kind=EntityKind.CLOUD,
                data=pcd,
                scalar_field=sf,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            display_name="Curvature Estimation",
        )
