"""DBSCAN clustering.

Groups points into dense regions using the DBSCAN algorithm.  Points in
low-density regions are labelled as noise (-1).
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
        name="eps",
        label="Epsilon (Neighbourhood Radius)",
        type=ParamType.FLOAT,
        default=0.1,
        min=0.001,
        max=100.0,
        help="Maximum distance between two points to be in the same neighbourhood.",
    ),
    ParamSpec(
        name="min_points",
        label="Min Points",
        type=ParamType.INT,
        default=10,
        min=1,
        max=10000,
        help="Minimum number of points to form a dense region.",
    ),
)


class DBSCAN(AlgorithmBase):
    """DBSCAN clustering using Open3D."""

    id = "geometry.dbscan"
    name = "DBSCAN Clustering"
    category = "Geometry"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        eps: float = resolved["eps"]
        min_points: int = resolved["min_points"]

        import numpy as np

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind, ScalarField

        results = []
        diagnostics: dict[str, Any] = {}
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            pcd = entity.data
            if not isinstance(pcd, o3d.geometry.PointCloud):
                continue
            labels = np.array(pcd.cluster_dbscan(eps=eps, min_points=min_points))
            n_clusters = int(labels.max()) + 1
            n_noise = int((labels == -1).sum())
            logger.info(
                "DBSCAN %s: %d clusters, %d noise points",
                entity.name,
                n_clusters,
                n_noise,
            )
            sf = ScalarField(name="cluster_label", values=labels.astype(np.float64))
            out = Entity(
                name=f"{entity.name} (DBSCAN)",
                kind=EntityKind.CLOUD,
                data=pcd,
                scalar_field=sf,
            )
            results.append(out)
            diagnostics["n_clusters"] = n_clusters
            diagnostics["n_noise"] = n_noise

        return AlgorithmResult(
            entities=results,
            diagnostics=diagnostics,
            display_name="DBSCAN Clustering",
        )
