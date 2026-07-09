"""Region-growing segmentation.

Starting from seed points, grows segments by adding neighbouring points
that satisfy normal-direction and curvature smoothness constraints.

This is a simplified approximation — a full implementation follows the
CloudCompare region-growing strategy.
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
        name="search_radius",
        label="Search Radius",
        type=ParamType.FLOAT,
        default=0.1,
        min=0.001,
        max=100.0,
    ),
    ParamSpec(
        name="angle_threshold_deg",
        label="Angle Threshold (°)",
        type=ParamType.FLOAT,
        default=10.0,
        min=0.1,
        max=90.0,
        help="Maximum angle between neighbouring normals to merge into the same segment.",
    ),
    ParamSpec(
        name="curvature_threshold",
        label="Curvature Threshold",
        type=ParamType.FLOAT,
        default=0.01,
        min=0.0,
        max=1.0,
        help="Maximum local curvature for a point to be a region seed.",
    ),
)


class RegionGrowing(AlgorithmBase):
    """Region-growing segmentation (approximation)."""

    id = "geometry.region_growing"
    name = "Region Growing"
    category = "Geometry"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        # For now, delegate to DBSCAN-like labelling as a placeholder.
        # A full region-growing implementation will use normal consistency.
        logger.warning(
            "RegionGrowing: using DBSCAN fallback. "
            "Full region-growing not yet implemented."
        )
        from pccm.algorithms.geometry.dbscan import DBSCAN

        dbscan = DBSCAN()
        params = {
            "eps": resolved["search_radius"],
            "min_points": 3,
        }
        return dbscan.run(ctx, **params)
