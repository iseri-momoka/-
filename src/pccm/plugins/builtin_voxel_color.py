"""Built-in example plugin: voxel downsample with a colour override.

Demonstrates how to add an algorithm without touching the core tree.
"""

from __future__ import annotations

from pccm.algorithms.base import (
    AlgorithmBase,
    AlgorithmResult,
    ParamSpec,
    ParamType,
    RunContext,
)
from pccm.plugins.api import register

PARAMS = (
    ParamSpec(
        "source",
        "Source cloud",
        ParamType.POINT_CLOUD_REF,
        default="",
        help="Entity id of the point cloud to downsample.",
    ),
    ParamSpec(
        "voxel_size",
        "Voxel size",
        ParamType.FLOAT,
        default=0.05,
        min=1e-5,
        max=10.0,
    ),
    ParamSpec(
        "color",
        "Override colour",
        ParamType.VECTOR3,
        default=(0.8, 0.4, 0.2),
        help="RGB triple in [0,1] applied to all points.",
    ),
)


class VoxelColorDownsample(AlgorithmBase):
    id = "plugin.voxel_color"
    name = "Voxel Downsample + Color (Example Plugin)"
    category = "Plugins / Builtin"
    params = PARAMS

    def run(self, ctx: RunContext, **values) -> AlgorithmResult:
        import numpy as np

        pcd = ctx.document.get(values["source"]).data
        voxel = float(values["voxel_size"])
        down = pcd.voxel_down_sample(voxel)
        r, g, b = values["color"]
        n = len(down.points)
        down.colors = o3d_obj()  # placeholder; will be replaced below
        try:
            import open3d as o3d

            down.colors = o3d.utility.Vector3dVector(
                np.tile([r, g, b], (n, 1))
            )
        except Exception:
            pass
        return AlgorithmResult(
            entities=[],
            scalar_field=None,
            transform=None,
            diagnostics={"input_points": len(pcd.points), "output_points": n},
            display_name=f"voxel_color[{voxel}]",
        )


def o3d_obj() -> object:
    import open3d as o3d

    return o3d.utility.Vector3dVector()


register(VoxelColorDownsample())
