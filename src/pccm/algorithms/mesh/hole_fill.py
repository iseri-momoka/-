"""Automatic hole filling for triangle meshes.

Detects boundary edges and fills the enclosed holes with new triangles.
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
        name="hole_size",
        label="Hole Size",
        type=ParamType.INT,
        default=10000,
        min=1,
        max=1000000,
        help="Maximum area (in triangle count equivalent) of hole to fill.",
    ),
)


class FillHoles(AlgorithmBase):
    """Hole filling using Open3D."""

    id = "mesh.hole_fill"
    name = "Fill Holes"
    category = "Mesh"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        hole_size: int = resolved["hole_size"]

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            mesh = entity.data
            if not isinstance(mesh, o3d.geometry.TriangleMesh):
                logger.warning("Skipping non-mesh entity %s", entity.name)
                continue
            filled = mesh.fill_holes(hole_size=hole_size)
            logger.info(
                "Fill holes %s: %d vertices, %d triangles",
                entity.name,
                len(filled.vertices),
                len(filled.triangles),
            )
            ctx.report(1.0, f"Filled holes: {len(filled.triangles)} triangles")
            out = Entity(
                name=f"{entity.name} (hole-filled)",
                kind=EntityKind.MESH,
                data=filled,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            display_name="Fill Holes",
        )
