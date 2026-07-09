"""Cloud-to-mesh distance.

Computes, for each point in a cloud, the distance to the nearest
triangle in a mesh.
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
        name="cloud_id",
        label="Source Cloud",
        type=ParamType.POINT_CLOUD_REF,
        default=None,
    ),
    ParamSpec(
        name="mesh_id",
        label="Target Mesh",
        type=ParamType.MESH_REF,
        default=None,
    ),
    ParamSpec(
        name="abs_distance",
        label="Absolute Distance",
        type=ParamType.BOOL,
        default=False,
        help="If true, return absolute distances; otherwise signed (towards normals).",
    ),
)


class CloudToMeshDistance(AlgorithmBase):
    """Cloud-to-mesh distance using Open3D."""

    id = "distance.cloud_to_mesh"
    name = "Cloud-to-Mesh Distance"
    category = "Distance"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        cloud_id: str | None = resolved["cloud_id"]
        mesh_id: str | None = resolved["mesh_id"]
        abs_dist: bool = resolved["abs_distance"]

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind, ScalarField

        if cloud_id is None or mesh_id is None:
            if len(ctx.selected_ids) < 2:
                raise ValueError("C2M distance requires a cloud and a mesh")
            # Attempt to infer from selection
            for eid in ctx.selected_ids:
                ent = ctx.document.get(eid)
                if ent and isinstance(ent.data, o3d.geometry.PointCloud):
                    cloud_id = cloud_id or eid
                elif ent and isinstance(ent.data, o3d.geometry.TriangleMesh):
                    mesh_id = mesh_id or eid

        cloud_entity = ctx.document.get_or_raise(cloud_id)
        mesh_entity = ctx.document.get_or_raise(mesh_id)
        pcd: o3d.geometry.PointCloud = cloud_entity.data
        mesh: o3d.geometry.TriangleMesh = mesh_entity.data

        distances = np.asarray(
            mesh.compute_point_cloud_distance(pcd, abs_distance=abs_dist)
        )
        sf = ScalarField(name="c2m_distance", values=distances)
        out = Entity(
            name=f"{cloud_entity.name} (C2M)",
            kind=EntityKind.CLOUD,
            data=pcd,
            scalar_field=sf,
        )
        diagnostics: dict[str, Any] = {
            "max_distance": float(distances.max()),
            "mean_distance": float(distances.mean()),
        }
        ctx.report(1.0, f"Max C2M distance: {distances.max():.6f}")

        return AlgorithmResult(
            entities=[out],
            diagnostics=diagnostics,
            display_name="Cloud-to-Mesh Distance",
        )
