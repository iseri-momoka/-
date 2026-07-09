"""Global registration via FPFH features + RANSAC.

Computes FPFH descriptors on both clouds, then uses RANSAC to find a
rigid transformation alignment without requiring an initial guess.
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
        name="source_id",
        label="Source Cloud",
        type=ParamType.POINT_CLOUD_REF,
        default=None,
    ),
    ParamSpec(
        name="target_id",
        label="Target Cloud",
        type=ParamType.POINT_CLOUD_REF,
        default=None,
    ),
    ParamSpec(
        name="voxel_size",
        label="FPFH Voxel Size",
        type=ParamType.FLOAT,
        default=0.05,
        min=0.001,
        max=10.0,
        help="Voxel size used for downsampling before FPFH computation.",
    ),
    ParamSpec(
        name="max_iterations",
        label="RANSAC Iterations",
        type=ParamType.INT,
        default=100000,
        min=100,
        max=10000000,
    ),
    ParamSpec(
        name="max_correspondence_distance",
        label="Max Correspondence Distance",
        type=ParamType.FLOAT,
        default=0.15,
        min=0.001,
        max=100.0,
    ),
    ParamSpec(
        name="confidence",
        label="Confidence",
        type=ParamType.FLOAT,
        default=0.999,
        min=0.5,
        max=1.0,
    ),
)


class GlobalRANSACRegistration(AlgorithmBase):
    """FPFH + RANSAC global registration using Open3D."""

    id = "registration.global_ransac"
    name = "Global Registration (RANSAC)"
    category = "Registration"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        source_id: str | None = resolved["source_id"]
        target_id: str | None = resolved["target_id"]
        voxel_size: float = resolved["voxel_size"]
        max_iter: int = resolved["max_iterations"]
        max_corr_dist: float = resolved["max_correspondence_distance"]
        confidence: float = resolved["confidence"]

        import numpy as np

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind

        if source_id is None or target_id is None:
            if len(ctx.selected_ids) < 2:
                raise ValueError(
                    "Global registration requires two selected clouds"
                )
            source_id = source_id or ctx.selected_ids[0]
            target_id = target_id or ctx.selected_ids[1]

        source_entity = ctx.document.get_or_raise(source_id)
        target_entity = ctx.document.get_or_raise(target_id)
        source = source_entity.data
        target = target_entity.data

        if not isinstance(source, o3d.geometry.PointCloud) or not isinstance(
            target, o3d.geometry.PointCloud
        ):
            raise TypeError("Both source and target must be PointCloud")

        # Downsample for FPFH
        src_down = source.voxel_down_sample(voxel_size)
        tgt_down = target.voxel_down_sample(voxel_size)

        # Estimate normals
        radius_feature = voxel_size * 5
        src_down.estimate_normals(
            o3d.geometry.KDTreeSearchParamHybrid(
                radius=radius_feature, max_nn=100
            )
        )
        tgt_down.estimate_normals(
            o3d.geometry.KDTreeSearchParamHybrid(
                radius=radius_feature, max_nn=100
            )
        )

        # Compute FPFH features
        src_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
            src_down,
            o3d.geometry.KDTreeSearchParamHybrid(
                radius=radius_feature, max_nn=100
            ),
        )
        tgt_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
            tgt_down,
            o3d.geometry.KDTreeSearchParamHybrid(
                radius=radius_feature, max_nn=100
            ),
        )

        # RANSAC registration
        result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
            src_down,
            tgt_down,
            src_fpfh,
            tgt_fpfh,
            True,
            max_corr_dist,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
            3,
            [
                o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(
                    0.9
                ),
                o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(
                    max_corr_dist
                ),
            ],
            o3d.pipelines.registration.RANSACConvergenceCriteria(
                max_iter, confidence
            ),
        )

        transform = result.transformation
        fitness = result.fitness
        inlier_rmse = result.inlier_rmse
        logger.info(
            "Global RANSAC %s→%s: fitness=%.4f, rmse=%.6f",
            source_entity.name,
            target_entity.name,
            fitness,
            inlier_rmse,
        )
        ctx.report(1.0, f"Global RANSAC fitness={fitness:.4f}")

        out = Entity(
            name=f"{source_entity.name} (global aligned)",
            kind=EntityKind.CLOUD,
            data=source,
            transform=transform,
        )
        return AlgorithmResult(
            entities=[out],
            transform=transform,
            diagnostics={
                "fitness": float(fitness),
                "inlier_rmse": float(inlier_rmse),
            },
            display_name="Global RANSAC Registration",
        )
