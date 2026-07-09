"""M3C2-style signed distance computation.

A simplified version of the M3C2 algorithm that computes distances
between two clouds along surface normals, with optional multi-scale
analysis.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

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
        name="core_points_id",
        label="Core Points Cloud",
        type=ParamType.POINT_CLOUD_REF,
        default=None,
        help="Optional: points at which to compute distances. Defaults to source cloud.",
    ),
    ParamSpec(
        name="search_radius",
        label="Search Radius",
        type=ParamType.FLOAT,
        default=0.1,
        min=0.001,
        max=100.0,
    ),
    ParamSpec(
        name="normal_radius",
        label="Normal Estimation Radius",
        type=ParamType.FLOAT,
        default=0.2,
        min=0.001,
        max=100.0,
    ),
    ParamSpec(
        name="min_neighbors",
        label="Min Neighbours",
        type=ParamType.INT,
        default=5,
        min=1,
        max=1000,
    ),
)


class M3C2Distance(AlgorithmBase):
    """Simplified M3C2 signed distance between two point clouds."""

    id = "distance.m3c2"
    name = "M3C2 Distance"
    category = "Distance"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        source_id: str | None = resolved["source_id"]
        target_id: str | None = resolved["target_id"]
        core_id: str | None = resolved["core_points_id"]
        search_radius: float = resolved["search_radius"]
        normal_radius: float = resolved["normal_radius"]
        min_neighbors: int = resolved["min_neighbors"]

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind, ScalarField

        if source_id is None or target_id is None:
            if len(ctx.selected_ids) < 2:
                raise ValueError("M3C2 requires two selected clouds")
            source_id = source_id or ctx.selected_ids[0]
            target_id = target_id or ctx.selected_ids[1]

        src_entity = ctx.document.get_or_raise(source_id)
        tgt_entity = ctx.document.get_or_raise(target_id)
        src_pcd: o3d.geometry.PointCloud = src_entity.data
        tgt_pcd: o3d.geometry.PointCloud = tgt_entity.data

        # Core points (where we evaluate distances)
        if core_id:
            core_entity = ctx.document.get_or_raise(core_id)
            core_pcd: o3d.geometry.PointCloud = core_entity.data
        else:
            core_pcd = src_pcd

        # Ensure normals exist on target
        if not tgt_pcd.has_normals():
            tgt_pcd.estimate_normals(
                o3d.geometry.KDTreeSearchParamHybrid(
                    radius=normal_radius, max_nn=100
                )
            )

        core_points = np.asarray(core_pcd.points)
        core_normals = np.asarray(core_pcd.normals) if core_pcd.has_normals() else None
        tgt_points = np.asarray(tgt_pcd.points)
        tgt_normals = np.asarray(tgt_pcd.normals)

        tree = o3d.geometry.KDTreeFlann(tgt_pcd)
        distances = np.zeros(len(core_points))

        for i in range(len(core_points)):
            [_, idx, _] = tree.search_radius_vector_3d(core_points[i], search_radius)
            if len(idx) < min_neighbors:
                continue
            # Project target points along their normals, measure signed distance
            local_pts = tgt_points[idx]
            local_normals = tgt_normals[idx]
            diffs = local_pts - core_points[i]
            # Signed distance = dot product of diff with mean normal
            mean_normal = local_normals.mean(axis=0)
            norm = np.linalg.norm(mean_normal)
            if norm > 0:
                mean_normal /= norm
            signed_dists = diffs @ mean_normal
            # Use median for robustness
            distances[i] = float(np.median(signed_dists))

        sf = ScalarField(name="m3c2_distance", values=distances)
        out = Entity(
            name=f"{src_entity.name} (M3C2)",
            kind=EntityKind.CLOUD,
            data=core_pcd,
            scalar_field=sf,
        )
        diagnostics = {
            "max_abs_distance": float(np.abs(distances).max()),
            "mean_distance": float(distances.mean()),
        }
        ctx.report(1.0, f"M3C2 max |distance|: {np.abs(distances).max():.6f}")

        return AlgorithmResult(
            entities=[out],
            diagnostics=diagnostics,
            display_name="M3C2 Distance",
        )
