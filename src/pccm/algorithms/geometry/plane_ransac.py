"""RANSAC plane fitting.

Fits a plane to a point cloud using the RANSAC algorithm, then extracts
inliers and outliers as separate point clouds.
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
        name="distance_threshold",
        label="Distance Threshold",
        type=ParamType.FLOAT,
        default=0.01,
        min=0.0001,
        max=10.0,
        help="Maximum distance from a point to the plane to be an inlier.",
    ),
    ParamSpec(
        name="ransac_n",
        label="RANSAC Samples",
        type=ParamType.INT,
        default=3,
        min=3,
        max=100,
        help="Number of points sampled per iteration.",
    ),
    ParamSpec(
        name="num_iterations",
        label="Iterations",
        type=ParamType.INT,
        default=1000,
        min=10,
        max=100000,
        help="Number of RANSAC iterations.",
    ),
    ParamSpec(
        name="extract_outliers",
        label="Also Extract Outliers",
        type=ParamType.BOOL,
        default=True,
        help="If true, also output a cloud of outlier points.",
    ),
)


class PlaneRANSAC(AlgorithmBase):
    """RANSAC plane fitting using Open3D."""

    id = "geometry.plane_ransac"
    name = "Plane Fitting (RANSAC)"
    category = "Geometry"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        dist_thresh: float = resolved["distance_threshold"]
        ransac_n: int = resolved["ransac_n"]
        num_iter: int = resolved["num_iterations"]
        extract_outliers: bool = resolved["extract_outliers"]

        import numpy as np

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind

        results = []
        diagnostics: dict[str, Any] = {}
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            pcd = entity.data
            if not isinstance(pcd, o3d.geometry.PointCloud):
                continue
            plane_model, inlier_idx = pcd.segment_plane(
                distance_threshold=dist_thresh,
                ransac_n=ransac_n,
                num_iterations=num_iter,
            )
            inliers = pcd.select_by_index(inlier_idx)
            n_inliers = len(inlier_idx)
            a, b, c, d = plane_model
            logger.info(
                "Plane RANSAC %s: %d inliers, plane=[%.4f,%.4f,%.4f,%.4f]",
                entity.name,
                n_inliers,
                a,
                b,
                c,
                d,
            )
            out_inlier = Entity(
                name=f"{entity.name} (plane inliers)",
                kind=EntityKind.CLOUD,
                data=inliers,
                annotations={"plane_model": plane_model},
            )
            results.append(out_inlier)
            diagnostics["plane_model"] = [float(v) for v in plane_model]
            diagnostics["n_inliers"] = n_inliers

            if extract_outliers:
                outlier_idx = list(
                    set(range(len(pcd.points))) - set(inlier_idx)
                )
                outliers = pcd.select_by_index(outlier_idx)
                out_outlier = Entity(
                    name=f"{entity.name} (plane outliers)",
                    kind=EntityKind.CLOUD,
                    data=outliers,
                )
                results.append(out_outlier)
                diagnostics["n_outliers"] = len(outlier_idx)

        return AlgorithmResult(
            entities=results,
            diagnostics=diagnostics,
            display_name="Plane RANSAC",
        )
