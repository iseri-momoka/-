"""Tests for I/O round-trip: load → save → reload, checking fidelity."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from pccm.io.registry import registry as io_registry


def _make_cloud(n=500, seed=42):
    import open3d as o3d

    rng = np.random.default_rng(seed)
    pts = rng.random((n, 3)) * 10.0
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    return pcd


class TestPLYRoundTrip:
    def test_save_reload(self, tmp_path: Path):
        from pccm.io.ply_reader import PLYReader, PLYWriter

        pcd = _make_cloud(500)
        out = tmp_path / "out.ply"
        PLYWriter.write(pcd, out)
        assert out.exists()

        loaded = PLYReader.read(out)
        assert len(loaded.points) == len(pcd.points)
        np.testing.assert_allclose(
            np.asarray(loaded.points), np.asarray(pcd.points), atol=1e-5
        )


class TestPCDRoundTrip:
    def test_save_reload(self, tmp_path: Path):
        from pccm.io.pcd_reader import PCDReader, PCDWriter

        pcd = _make_cloud(300)
        out = tmp_path / "out.pcd"
        PCDWriter.write(pcd, out)
        assert out.exists()

        loaded = PCDReader.read(out)
        assert len(loaded.points) == len(pcd.points)


class TestFormatRegistry:
    def test_ply_registered(self):
        reader = io_registry.get_reader(".ply")
        writer = io_registry.get_writer(".ply")
        assert reader is not None
        assert writer is not None

    def test_pcd_registered(self):
        reader = io_registry.get_reader(".pcd")
        assert reader is not None
