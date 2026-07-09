"""Voxel grid downsampling.

Reduces point count by replacing all points within each voxel with their
centroid.  This is the fastest downsampling method and preserves overall
shape well.
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
        name="voxel_size",
        label="Voxel Size",
        type=ParamType.FLOAT,
        default=0.05,
        min=0.001,
        max=100.0,
        help="Edge length of each voxel in the same units as the point cloud.",
    ),
)


class VoxelDownsample(AlgorithmBase):
    """Voxel grid downsampling using Open3D."""

    id = "filter.voxel"
    name = "Voxel Downsampling"
    category = "Filter"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        voxel_size: float = resolved["voxel_size"]

        import open3d as o3d

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            pcd = entity.data
            if not isinstance(pcd, o3d.geometry.PointCloud):
                logger.warning("Skipping non-cloud entity %s", entity.name)
                continue
            original_count = len(pcd.points)
            down = pcd.voxel_down_sample(voxel_size)
            new_count = len(down.points)
            ctx.report(1.0, f"Downsampled {original_count} → {new_count} points")
            logger.info(
                "Voxel downsample %s: %d → %d (size=%.4f)",
                entity.name,
                original_count,
                new_count,
                voxel_size,
            )
            # Create a new entity for the result
            from pccm.core.types import Entity, EntityKind

            out = Entity(
                name=f"{entity.name} (voxel {voxel_size})",
                kind=EntityKind.CLOUD,
                data=down,
            )
            results.append(out)

        return AlgorithmResult(
            entities=results,
            diagnostics={"voxel_size": voxel_size},
            display_name="Voxel Downsample",
        )
