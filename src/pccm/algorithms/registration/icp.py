"""Iterative Closest Point (ICP) registration.

Supports point-to-point and point-to-plane variants with optional
initial alignment.
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
        help="The point cloud to be transformed.",
    ),
    ParamSpec(
        name="target_id",
        label="Target Cloud",
        type=ParamType.POINT_CLOUD_REF,
        default=None,
        help="The point cloud to align to.",
    ),
    ParamSpec(
        name="method",
        label="Method",
        type=ParamType.ENUM,
        default="point-to-point",
        options=("point-to-point", "point-to-plane"),
    ),
    ParamSpec(
        name="max_iterations",
        label="Max Iterations",
        type=ParamType.INT,
        default=100,
        min=1,
        max=10000,
    ),
    ParamSpec(
        name="tolerance",
        label="Convergence Tolerance",
        type=ParamType.FLOAT,
        default=1e-6,
        min=1e-10,
        max=1.0,
    ),
    ParamSpec(
        name="max_correspondence_distance",
        label="Max Correspondence Distance",
        type=ParamType.FLOAT,
        default=1.0,
        min=0.001,
        max=1000.0,
    ),
)


class ICPRegistration(AlgorithmBase):
    """ICP registration using Open3D pipelines."""

    id = "registration.icp"
    name = "ICP Registration"
    category = "Registration"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        source_id: str | None = resolved["source_id"]
        target_id: str | None = resolved["target_id"]
        method: str = resolved["method"]
        max_iter: int = resolved["max_iterations"]
        tol: float = resolved["tolerance"]
        max_corr_dist: float = resolved["max_correspondence_distance"]

        import numpy as np

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind

        # Resolve source and target from selected entities
        if source_id is None or target_id is None:
            if len(ctx.selected_ids) < 2:
                raise ValueError(
                    "ICP requires two selected clouds or explicit source/target"
                )
            source_id = source_id or ctx.selected_ids[0]
            target_id = target_id or ctx.selected_ids[1]

        source_entity = ctx.document.get_or_raise(source_id)
        target_entity = ctx.document.get_or_raise(target_id)
        source = source_entity.data
        target = target_entity.data

        if not isinstance(source, o3d.geometry.PointCloud):
            raise TypeError(f"Source must be PointCloud, got {type(source)}")
        if not isinstance(target, o3d.geometry.PointCloud):
            raise TypeError(f"Target must be PointCloud, got {type(target)}")

        # Build estimation method
        if method == "point-to-plane":
            target.estimate_normals(
                o3d.geometry.KDTreeSearchParamHybrid(
                    radius=max_corr_dist * 2, max_nn=30
                )
            )
            estimation = o3d.pipelines.registration.TransformationEstimationPointToPlane()
        else:
            estimation = o3d.pipelines.registration.TransformationEstimationPointToPoint()

        criteria = o3d.pipelines.registration.ICPConvergenceCriteria(
            relative_fitness=tol, relative_rmse=tol, max_iteration=max_iter
        )
        reg = o3d.pipelines.registration.registration_icp(
            source,
            target,
            max_corr_dist,
            np.eye(4),
            estimation,
            criteria,
        )

        transform = reg.transformation
        fitness = reg.fitness
        inlier_rmse = reg.inlier_rmse
        logger.info(
            "ICP %s→%s: fitness=%.4f, rmse=%.6f",
            source_entity.name,
            target_entity.name,
            fitness,
            inlier_rmse,
        )
        ctx.report(1.0, f"ICP fitness={fitness:.4f}, rmse={inlier_rmse:.6f}")

        out = Entity(
            name=f"{source_entity.name} (ICP aligned)",
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
                "method": method,
            },
            display_name="ICP Registration",
        )
