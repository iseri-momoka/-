"""Quadric edge-collapse decimation.

Reduces triangle count while preserving shape and topology as much as
possible.
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
        name="target_triangles",
        label="Target Triangle Count",
        type=ParamType.INT,
        default=10000,
        min=4,
        max=100000000,
    ),
    ParamSpec(
        name="maximum_error",
        label="Maximum Quadric Error",
        type=ParamType.FLOAT,
        default=0.0,
        min=0.0,
        max=100.0,
        help="Maximum allowed error per vertex (0 = unlimited).",
    ),
    ParamSpec(
        name="boundary_weight",
        label="Boundary Weight",
        type=ParamType.FLOAT,
        default=1.0,
        min=0.0,
        max=100.0,
        help="Weight given to boundary edges; higher preserves boundaries.",
    ),
)


class DecimateMesh(AlgorithmBase):
    """Quadric edge-collapse decimation using Open3D."""

    id = "mesh.decimate"
    name = "Decimate Mesh"
    category = "Mesh"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        target: int = resolved["target_triangles"]
        max_err: float = resolved["maximum_error"]
        boundary_weight: float = resolved["boundary_weight"]

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
            original_tris = len(mesh.triangles)
            simplified = mesh.simplify_quadric_decimation(
                target_number_of_triangles=target,
                maximum_error=max_err,
                boundary_weight=boundary_weight,
            )
            new_tris = len(simplified.triangles)
            logger.info(
                "Decimate %s: %d → %d triangles",
                entity.name,
                original_tris,
                new_tris,
            )
            ctx.report(1.0, f"Decimated: {original_tris} → {new_tris} triangles")
            out = Entity(
                name=f"{entity.name} (decimated)",
                kind=EntityKind.MESH,
                data=simplified,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            diagnostics={"target": target},
            display_name="Decimate Mesh",
        )
