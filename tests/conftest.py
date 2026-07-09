"""Test configuration — shared fixtures, markers, and path setup."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src/ is on the Python path so that `import pccm` works
# regardless of how tests are launched.
_root = Path(__file__).parent.parent
_src = _root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_ply(tmp_path: Path) -> Path:
    """Write a tiny 3-point PLY file to tmp_path and return its path."""
    content = (
        "ply\n"
        "format ascii 1.0\n"
        "element vertex 3\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "end_header\n"
        "0.0 0.0 0.0\n"
        "1.0 0.0 0.0\n"
        "0.0 1.0 0.0\n"
    )
    p = tmp_path / "small.ply"
    p.write_text(content)
    return p


@pytest.fixture()
def synthetic_cloud():
    """Create a small open3d PointCloud with 100 random points."""
    import numpy as np

    try:
        import open3d as o3d

        pts = np.random.default_rng(42).random((100, 3))
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(pts)
        return cloud
    except ImportError:
        pytest.skip("open3d not installed")


@pytest.fixture()
def two_clouds_for_icp():
    """Two point clouds separated by a known transformation for ICP tests."""
    import numpy as np

    try:
        import open3d as o3d

        rng = np.random.default_rng(42)
        base = rng.random((200, 3))
        cloud_a = o3d.geometry.PointCloud()
        cloud_a.points = o3d.utility.Vector3dVector(base)

        # Apply a 5° rotation around Z + small translation
        angle = np.radians(5)
        R = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle),  np.cos(angle), 0],
            [0,              0,             1],
        ])
        t = np.array([0.02, -0.01, 0.005])
        cloud_b = o3d.geometry.PointCloud()
        cloud_b.points = o3d.utility.Vector3dVector((R @ base.T).T + t)

        return cloud_a, cloud_b, R, t
    except ImportError:
        pytest.skip("open3d not installed")
