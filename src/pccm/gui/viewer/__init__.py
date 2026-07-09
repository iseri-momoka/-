"""Viewer package: 3D viewer widgets and scene management.

- o3d_widget — Open3D → Qt offscreen FBO bridge
- scene — Document ↔ Open3D geometry synchronisation
- camera — camera presets and animation helpers
- overlay — on-screen text / annotation overlay
"""

from pccm.gui.viewer.o3d_widget import Open3DWidget  # noqa: F401

__all__ = ["Open3DWidget"]
