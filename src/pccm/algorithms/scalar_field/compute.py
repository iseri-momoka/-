"""Compute a derived scalar field on a point cloud.

For example: distance to origin, height (Z), projection along a custom
direction, etc.
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
        name="mode",
        label="Mode",
        type=ParamType.ENUM,
        default="height",
        options=("height", "distance_to_origin", "x", "y", "z"),
    ),
    ParamSpec(
        name="output_name",
        label="Output Scalar Field Name",
        type=ParamType.STRING,
        default="",
        help="If empty, defaults to mode name.",
    ),
)


class ComputeScalarField(AlgorithmBase):
    """Compute a derived scalar field (height, distance, axis, etc.)."""

    id = "scalar_field.compute"
    name = "Compute Scalar Field"
    category = "Scalar Field"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        mode: str = resolved["mode"]
        out_name: str = resolved["output_name"] or mode

        import open3d as o3d
        from pccm.core.types import Entity, EntityKind, ScalarField

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None or not isinstance(
                entity.data, o3d.geometry.PointCloud
            ):
                continue
            points = np.asarray(entity.data.points)
            if points.size == 0:
                continue
            if mode == "height" or mode == "z":
                values = points[:, 2]
            elif mode == "x":
                values = points[:, 0]
            elif mode == "y":
                values = points[:, 1]
            elif mode == "distance_to_origin":
                values = np.linalg.norm(points, axis=1)
            else:
                continue
            sf = ScalarField(name=out_name, values=values)
            out = Entity(
                name=f"{entity.name} (scalar)",
                kind=EntityKind.CLOUD,
                data=entity.data,
                scalar_field=sf,
            )
            results.append(out)
            ctx.report(1.0, f"Computed scalar field: {out_name}")

        return AlgorithmResult(
            entities=results,
            display_name="Compute Scalar Field",
        )
