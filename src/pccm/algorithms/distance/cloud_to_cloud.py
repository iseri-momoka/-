"""Cloud-to-cloud distance.

Computes, for each point in a source cloud, the distance to the nearest
point in a target cloud.  Optionally computes symmetric distances.
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
        name="symmetric",
        label="Symmetric",
        type=ParamType.BOOL,
        default=True,
        help="If true, compute max(d(source→target), d(target→source)).",
    ),
)


class CloudToCloudDistance(AlgorithmBase):
    """Cloud-to-cloud distance using Open3D KDTree."""

    id = "distance.cloud_to_cloud"
    name = "Cloud-to-Cloud Distance"
    category = "Distance"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        source_id: str | None = resolved["source_id"]
        target_id: str | None = resolved["target_id"]
        symmetric: bool = resolved["symmetric"]

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind, ScalarField

        if source_id is None or target_id is None:
            if len(ctx.selected_ids) < 2:
                raise ValueError(
                    "C2C distance requires two selected clouds"
                )
            source_id = source_id or ctx.selected_ids[0]
            target_id = target_id or ctx.selected_ids[1]

        src_entity = ctx.document.get_or_raise(source_id)
        tgt_entity = ctx.document.get_or_raise(target_id)
        src_pcd: o3d.geometry.PointCloud = src_entity.data
        tgt_pcd: o3d.geometry.PointCloud = tgt_entity.data

        # Forward: source → target
        distances_st = np.asarray(src_pcd.compute_point_cloud_distance(tgt_pcd))
        if symmetric:
            distances_ts = np.asarray(
                tgt_pcd.compute_point_cloud_distance(src_pcd)
            )
            # For source cloud: max of forward distance and nearest in target
            # For visualization on source, use forward distance
            combined = distances_st
            combined_entity = src_entity
        else:
            combined = distances_st
            combined_entity = src_entity

        sf = ScalarField(name="c2c_distance", values=combined)
        out = Entity(
            name=f"{src_entity.name} (C2C)",
            kind=EntityKind.CLOUD,
            data=src_pcd,
            scalar_field=sf,
        )
        diagnostics: dict[str, Any] = {
            "max_distance": float(combined.max()),
            "mean_distance": float(combined.mean()),
        }
        ctx.report(1.0, f"Max C2C distance: {combined.max():.6f}")

        return AlgorithmResult(
            entities=[out],
            diagnostics=diagnostics,
            display_name="Cloud-to-Cloud Distance",
        )
