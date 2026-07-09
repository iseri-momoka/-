"""Poisson surface reconstruction.

Reconstructs a watertight triangle mesh from an oriented point cloud
using the Poisson equation.  Requires surface normals.
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
        name="depth",
        label="Octree Depth",
        type=ParamType.INT,
        default=9,
        min=1,
        max=12,
        help="Maximum depth of the octree; higher = finer detail.",
    ),
    ParamSpec(
        name="scale",
        label="Scale",
        type=ParamType.FLOAT,
        default=1.1,
        min=1.0,
        max=3.0,
        help="Radius factor of the bounding cube.",
    ),
    ParamSpec(
        name="density_quantile",
        label="Density Quantile",
        type=ParamType.FLOAT,
        default=0.01,
        min=0.0,
        max=0.5,
        help="Points with density below this quantile are removed.",
    ),
)


class PoissonReconstruction(AlgorithmBase):
    """Poisson surface reconstruction using Open3D."""

    id = "mesh.poisson"
    name = "Poisson Reconstruction"
    category = "Mesh"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        depth: int = resolved["depth"]
        scale: float = resolved["scale"]
        density_quantile: float = resolved["density_quantile"]

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            pcd = entity.data
            if not isinstance(pcd, o3d.geometry.PointCloud):
                logger.warning("Skipping non-cloud entity %s", entity.name)
                continue
            # Estimate normals if not present
            if not pcd.has_normals():
                pcd.estimate_normals(
                    o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
                )
            mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                pcd, depth=depth, scale=scale
            )
            # Remove low-density vertices
            densities = np.asarray(densities)
            density_threshold = np.quantile(densities, density_quantile)
            vertices_to_remove = densities < density_threshold
            mesh.remove_vertices_by_mask(vertices_to_remove)
            mesh.compute_vertex_normals()
            logger.info(
                "Poisson %s: depth=%d, vertices=%d, triangles=%d",
                entity.name,
                depth,
                len(mesh.vertices),
                len(mesh.triangles),
            )
            ctx.report(1.0, f"Poisson: {len(mesh.vertices)} vertices")
            out = Entity(
                name=f"{entity.name} (Poisson mesh)",
                kind=EntityKind.MESH,
                data=mesh,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            diagnostics={"depth": depth, "scale": scale},
            display_name="Poisson Reconstruction",
        )
