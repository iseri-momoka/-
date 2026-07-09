"""Compute histogram of a scalar field.

Provides bin edges and counts for visualization in the histogram panel.
This is a pure computation — it does not modify the entity.
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
        name="nbins",
        label="Number of Bins",
        type=ParamType.INT,
        default=256,
        min=2,
        max=10000,
    ),
)


class ComputeHistogram(AlgorithmBase):
    """Compute histogram data for an entity's scalar field or coordinates."""

    id = "scalar_field.histogram"
    name = "Compute Histogram"
    category = "Scalar Field"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        nbins: int = resolved["nbins"]

        from pccm.core.types import Entity, EntityKind, ScalarField

        import open3d as o3d

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            values_arr: np.ndarray
            if entity.scalar_field is not None:
                values_arr = entity.scalar_field.values
            elif isinstance(entity.data, o3d.geometry.PointCloud):
                values_arr = np.asarray(entity.data.points)[:, 2]  # height
            else:
                continue
            counts, edges = np.histogram(values_arr, bins=nbins)
            diagnostics: dict[str, Any] = {
                "histogram": {
                    "counts": counts.tolist(),
                    "edges": edges.tolist(),
                    "nbins": int(nbins),
                }
            }
            out = Entity(
                name=f"{entity.name} (histogram)",
                kind=EntityKind.ANNOTATION,
                data=diagnostics,
            )
            results.append(out)
            ctx.report(1.0, f"Histogram: {nbins} bins")

        return AlgorithmResult(
            entities=results,
            display_name="Histogram",
        )
