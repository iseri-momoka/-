"""Colorize a point cloud using a scalar field and a matplotlib colormap.

Maps each point's scalar value to an RGB colour via a matplotlib colormap,
then stores the result as per-point colours on the cloud.
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
        name="scalar_field_name",
        label="Scalar Field Name",
        type=ParamType.STRING,
        default="height",
        help="Name of the scalar field to colorize (or 'height').",
    ),
    ParamSpec(
        name="colormap",
        label="Colormap",
        type=ParamType.ENUM,
        default="viridis",
        options=(
            "viridis",
            "plasma",
            "coolwarm",
            "jet",
            "rainbow",
            "terrain",
            "RdYlBu",
        ),
    ),
    ParamSpec(
        name="range_min",
        label="Range Min",
        type=ParamType.FLOAT,
        default=0.0,
    ),
    ParamSpec(
        name="range_max",
        label="Range Max",
        type=ParamType.FLOAT,
        default=0.0,
        help="Set to 0 to auto-detect from data range.",
    ),
)


class ColorizeByScalar(AlgorithmBase):
    """Apply a matplotlib colormap to an entity's scalar field."""

    id = "scalar_field.colorize"
    name = "Colorize by Scalar Field"
    category = "Scalar Field"
    params = PARAMS

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        resolved = self.validate_params(**values)
        sf_name: str = resolved["scalar_field_name"]
        cmap_name: str = resolved["colormap"]
        range_min: float = resolved["range_min"]
        range_max: float = resolved["range_max"]

        import matplotlib.cm as cm
        import open3d as o3d
        from pccm.core.types import Entity, EntityKind

        results = []
        for eid in ctx.selected_ids:
            entity = ctx.document.get(eid)
            if entity is None:
                continue
            # Get scalar values
            scalars: np.ndarray | None = None
            if entity.scalar_field is not None and entity.scalar_field.name == sf_name:
                scalars = entity.scalar_field.values
            elif sf_name == "height" and isinstance(
                entity.data, o3d.geometry.PointCloud
            ):
                points = np.asarray(entity.data.points)
                if len(points) > 0:
                    scalars = points[:, 2]
            if scalars is None:
                logger.warning(
                    "Entity %s has no scalar field named %r", entity.name, sf_name
                )
                continue
            # Normalize to [0, 1]
            vmin = range_min if range_min != 0.0 else scalars.min()
            vmax = range_max if range_max != 0.0 else scalars.max()
            if vmax <= vmin:
                vmax = vmin + 1.0
            norm = np.clip((scalars - vmin) / (vmax - vmin), 0.0, 1.0)
            # Apply colormap
            cmap = cm.get_cmap(cmap_name)
            rgba = cmap(norm)  # (N, 4) float in [0,1]
            rgb = rgba[:, :3].astype(np.float64)
            # Assign to cloud colours
            import open3d as o3d

            if isinstance(entity.data, o3d.geometry.PointCloud):
                import open3d as o3d_mod

                entity.data.colors = o3d_mod.utility.Vector3dVector(rgb)
            out = Entity(
                name=f"{entity.name} ({cmap_name})",
                kind=EntityKind.CLOUD,
                data=entity.data,
            )
            results.append(out)
            ctx.report(1.0, f"Colorized with {cmap_name}")

        return AlgorithmResult(
            entities=results,
            display_name="Colorize by Scalar",
        )
