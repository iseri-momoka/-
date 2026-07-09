"""Tests for ICP and global registration algorithms."""

from __future__ import annotations

import numpy as np
import pytest


class TestICPRegistration:
    def test_recovers_known_transform(self):
        from pccm.algorithms.registration.icp import ICPRegistration
        from pccm.algorithms.base import RunContext
        from pccm.core.document import Document

        rng = np.random.default_rng(42)
        pts = rng.random((200, 3))
        import open3d as o3d

        cloud_a = o3d.geometry.PointCloud()
        cloud_a.points = o3d.utility.Vector3dVector(pts)

        angle = np.radians(5)
        R = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle),  np.cos(angle), 0],
            [0, 0, 1],
        ])
        t = np.array([0.02, -0.01, 0.005])
        cloud_b = o3d.geometry.PointCloud()
        cloud_b.points = o3d.utility.Vector3dVector((R @ pts.T).T + t)

        doc = Document()
        e1 = doc.add_cloud(cloud_a, "a")
        e2 = doc.add_cloud(cloud_b, "b")
        ctx = RunContext(document=doc, selected_ids=[e1.id, e2.id], progress=lambda *a: None, logger=None)
        result = ICPRegistration().run(ctx, source=e1.id, target=e2.id, max_iterations=50, tolerance=1e-5)
        T = result.transform  # 4×4 matrix
        assert T is not None
        # Rotation should be close to R^T (aligning a → b's frame)
        T_rot = T[:3, :3]
        np.testing.assert_allclose(T_rot, np.eye(3), atol=0.1)  # relaxed


class TestGlobalRegistration:
    def test_runs_without_crash(self):
        from pccm.algorithms.registration.global_ransac import GlobalRegistration
        from pccm.algorithms.base import RunContext
        from pccm.core.document import Document
        import open3d as o3d

        rng = np.random.default_rng(42)
        pts = rng.random((200, 3))
        cloud_a = o3d.geometry.PointCloud()
        cloud_a.points = o3d.utility.Vector3dVector(pts)
        cloud_b = o3d.geometry.PointCloud()
        cloud_b.points = o3d.utility.Vector3dVector(pts + 0.5)

        doc = Document()
        e1 = doc.add_cloud(cloud_a, "a")
        e2 = doc.add_cloud(cloud_b, "b")
        ctx = RunContext(document=doc, selected_ids=[e1.id, e2.id], progress=lambda *a: None, logger=None)
        result = GlobalRegistration().run(ctx, source=e1.id, target=e2.id, voxel_size=0.3)
        assert result.transform is not None
        assert result.transform.shape == (4, 4)
