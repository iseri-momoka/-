"""Camera preset and view helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pccm.gui.viewer.o3d_widget import Open3DWidget


@dataclass
class CameraPreset:
    """A named camera position."""

    name: str
    eye: tuple[float, float, float]
    center: tuple[float, float, float]
    up: tuple[float, float, float]


# Common viewpoints
FRONT = CameraPreset("Front", (0, 0, 2), (0, 0, 0), (0, 1, 0))
BACK = CameraPreset("Back", (0, 0, -2), (0, 0, 0), (0, 1, 0))
TOP = CameraPreset("Top", (0, 2, 0), (0, 0, 0), (0, 0, -1))
RIGHT = CameraPreset("Right", (2, 0, 0), (0, 0, 0), (0, 1, 0))


def apply_preset(widget: Open3DWidget, preset: CameraPreset) -> None:
    """Apply a camera preset to the widget's view."""
    vc = widget._vis.get_view_control()
    vc.set_lookat(list(preset.center))
    vc.set_front(list(preset.eye))
    vc.set_up(list(preset.up))
