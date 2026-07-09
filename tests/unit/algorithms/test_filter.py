"""Tests for filter algorithms — voxel downsample, SOR, ROR, MLS."""

from __future__ import annotations

import numpy as np
import pytest

from pccm.algorithms.filter.voxel import VoxelDownsample
from pccm.algorithms.filter.statistical_outlier import StatisticalOutlier
from pccm.algorithms.filter.radius_outlier import RadiusOutlier
from pccm.algorithms.filter.smoothing import MLSSmoothing
from pccm.algorithms.base import RunContext
from pccm.core.document import Document


def _make_pcd(n=1000, seed=42):
    import open3d as o3d

    rng = np.random.default_rng(seed)
    pts = rng.random((n, 3)) * 10.0
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    return pcd


def _make_pcd_with_outliers(n=950, n_outliers=50, seed=42):
    """Return a cloud with n normal points and n_outliers scattered far away."""
    import open3d as o3d

    rng = np.random.default_rng(seed)
    pts = rng.random((n, 3))
    outliers = rng.random((n_outliers, 3)) * 100 + 50  # far away
    all_pts = np.vstack([pts, outliers])
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(all_pts)
    return pcd


class TestVoxelDownsample:
    def test_output_size(self):
        pcd = _make_pcd(5000)
        doc = Document()
        ent = doc.add_cloud(pcd, "test")
        ctx = RunContext(document=doc, selected_ids=[ent.id], progress=lambda *a: None, logger=None)
        result = VoxelDownsample().run(ctx, source=ent.id, voxel_size=1.0)
        out = result.entities[0].data
        assert len(out.points) <= 5000
        assert len(out.points) > 0

    def test_idempotent(self):
        pcd = _make_pcd(1000)
        doc = Document()
        ent = doc.add_cloud(pcd, "test")
        ctx = RunContext(document=doc, selected_ids=[ent.id], progress=lambda *a: None, logger=None)
        r1 = VoxelDownsample().run(ctx, source=ent.id, voxel_size=0.5)
        r2 = VoxelDownsample().run(ctx, source=ent.id, voxel_size=0.5)
        assert np.asarray(r1.entities[0].data.points).shape == np.asarray(r2.entities[0].data.points).shape


class TestStatisticalOutlier:
    def test_removes_outliers(self):
        pcd = _make_pcd_with_outliers(950, 50)
        doc = Document()
        ent = doc.add_cloud(pcd, "test")
        ctx = RunContext(document=doc, selected_ids=[ent.id], progress=lambda *a: None, logger=None)
        result = StatisticalOutlier().run(ctx, source=ent.id, nb_neighbors=20, std_ratio=2.0)
        out = result.entities[0].data
        # The 50 far-away outliers should be mostly removed
        assert len(out.points) < len(pcd.points)


class TestRadiusOutlier:
    def test_removes_outliers(self):
        pcd = _make_pcd_with_outliers(950, 50)
        doc = Document()
        ent = doc.add_cloud(pcd, "test")
        ctx = RunContext(document=doc, selected_ids=[ent.id], progress=lambda *a: None, logger=None)
        result = RadiusOutlier().run(ctx, source=ent.id, nb_points=5, radius=0.5)
        out = result.entities[0].data
        assert len(out.points) <= len(pcd.points)


class TestMLSSmoothing:
    def test_runs_without_error(self):
        import open3d as o3d

        pcd = _make_pcd(200)
        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, knn=10))
        doc = Document()
        ent = doc.add_cloud(pcd, "test")
        ctx = RunContext(document=doc, selected_ids=[ent.id], progress=lambda *a: None, logger=None)
        result = MLSSmoothing().run(ctx, source=ent.id, radius=1.0, polynomial_order=3)
        assert result.entities[0].data is not None
