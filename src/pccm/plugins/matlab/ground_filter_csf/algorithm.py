"""Cloth Simulation Filter (CSF) — ground point filter ported from MATLAB.

This is a Python re-implementation of the well-known CSF ground
filter.  It is wrapped as a PCCM plugin so that the legacy MATLAB
implementation can be replaced incrementally.

Reference
---------
W. Zhang, J. Qi, P. Wan, H. Wang, D. Xie, X. Wang, G. Yan,
"An Easy-to-Use Airborne LiDAR Data Filtering Method Based on Cloth
Simulation," Remote Sensing, 2016, 8(6): 501.
"""

from __future__ import annotations

import numpy as np

from pccm.algorithms.base import (
    AlgorithmBase,
    AlgorithmResult,
    ParamSpec,
    ParamType,
    RunContext,
)
from pccm.core.types import ScalarField
from pccm.plugins.api import register

PARAMS = (
    ParamSpec(
        "source",
        "Source cloud",
        ParamType.POINT_CLOUD_REF,
        default="",
    ),
    ParamSpec(
        "threshold",
        "Cloth threshold",
        ParamType.FLOAT,
        default=0.5,
        min=0.01,
        max=5.0,
        help="Maximum distance from cloth to count a point as ground.",
    ),
    ParamSpec(
        "iterations",
        "Iterations",
        ParamType.INT,
        default=500,
        min=10,
        max=10000,
    ),
    ParamSpec(
        "cloth_resolution",
        "Cloth resolution",
        ParamType.FLOAT,
        default=0.5,
        min=0.05,
        max=5.0,
    ),
    ParamSpec(
        "rigidness",
        "Rigidness",
        ParamType.INT,
        default=1,
        min=1,
        max=3,
        help="1 = spring, 2 = hammer, 3 = mixed.",
    ),
)


def _csf_core(
    points: np.ndarray,
    threshold: float,
    iterations: int,
    cloth_resolution: float,
    rigidness: int,
) -> np.ndarray:
    """Simplified CSF-like ground filter.

    This is a *placeholder* implementation: it projects the points onto
    a horizontal grid, takes the lowest non-empty cell as the cloth
    height, and labels all points within ``threshold`` of that surface
    as ground.  Real CSF uses an iterative cloth simulation.  The
    scaffolding is in place to swap in the full implementation later.
    """
    n = len(points)
    is_ground = np.zeros(n, dtype=bool)
    if n == 0:
        return is_ground

    # Cloth: discretize XY plane, store min Z per cell
    xy = points[:, :2]
    xy_min = xy.min(axis=0)
    xy_max = xy.max(axis=0)
    span = (xy_max - xy_min).max()
    if span <= 0:
        return np.ones(n, dtype=bool)

    cell = cloth_resolution
    nx = max(1, int(np.ceil((xy_max[0] - xy_min[0]) / cell)) + 1)
    ny = max(1, int(np.ceil((xy_max[1] - xy_min[1]) / cell)) + 1)
    cloth = np.full((nx, ny), np.inf)

    idx_x = np.clip(((xy[:, 0] - xy_min[0]) / cell).astype(int), 0, nx - 1)
    idx_y = np.clip(((xy[:, 1] - xy_min[1]) / cell).astype(int), 0, ny - 1)
    for i in range(n):
        ix, iy = idx_x[i], idx_y[i]
        if points[i, 2] < cloth[ix, iy]:
            cloth[ix, iy] = points[i, 2]

    # Label ground
    for i in range(n):
        ix, iy = idx_x[i], idx_y[i]
        if abs(points[i, 2] - cloth[ix, iy]) <= threshold:
            is_ground[i] = True
    # `iterations` and `rigidness` are accepted but unused in the simplified
    # core; preserved for API compatibility with the full CSF implementation.
    _ = (iterations, rigidness)
    return is_ground


class GroundFilterCSF(AlgorithmBase):
    id = "matlab.ground_filter_csf"
    name = "CSF Ground Filter (MATLAB port)"
    category = "Plugins / MATLAB"
    params = PARAMS

    def run(self, ctx: RunContext, **values) -> AlgorithmResult:
        entity = ctx.document.get(values["source"])
        if entity is None:
            raise ValueError(f"Entity not found: {values['source']}")
        points = np.asarray(entity.data.points)
        if points.size == 0:
            return AlgorithmResult(
                entities=[],
                scalar_field=ScalarField(name="ground_class", values=np.zeros(0, dtype=np.int8)),
                transform=None,
                diagnostics={"ground_points": 0},
                display_name="csf",
            )

        is_ground = _csf_core(
            points,
            threshold=float(values["threshold"]),
            iterations=int(values["iterations"]),
            cloth_resolution=float(values["cloth_resolution"]),
            rigidness=int(values["rigidness"]),
        )
        labels = is_ground.astype(np.int8)
        return AlgorithmResult(
            entities=[],
            scalar_field=ScalarField(name="ground_class", values=labels),
            transform=None,
            diagnostics={
                "ground_points": int(is_ground.sum()),
                "non_ground_points": int((~is_ground).sum()),
            },
            display_name="csf",
        )


register(GroundFilterCSF())
