"""Profile the offscreen Open3D render loop.

Measures frame time and CPU usage of Open3DWidget's blit pipeline::

    python scripts/profile_viewer.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np


def make_cloud(n: int = 200_000):
    import open3d as o3d

    rng = np.random.default_rng(42)
    pts = rng.random((n, 3)) * 10
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    return pcd


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("PySide6 not installed; skipping.")
        return 1

    from pccm.gui.viewer.o3d_widget import Open3DWidget

    app = QApplication.instance() or QApplication([])
    widget = Open3DWidget()
    widget.resize(1280, 720)
    widget.show()

    pcd = make_cloud(200_000)
    widget.add_geometry("test", pcd)
    widget._vis.reset_view_point(True)

    # Warm up
    for _ in range(5):
        widget._tick()
        app.processEvents()

    # Measure
    n_frames = 60
    t0 = time.perf_counter()
    for _ in range(n_frames):
        widget._tick()
        app.processEvents()
    elapsed = time.perf_counter() - t0

    fps = n_frames / elapsed
    avg_ms = 1000 * elapsed / n_frames
    print(f"Average frame: {avg_ms:.2f} ms ({fps:.1f} FPS) over {n_frames} frames")
    return 0


if __name__ == "__main__":
    sys.exit(main())
