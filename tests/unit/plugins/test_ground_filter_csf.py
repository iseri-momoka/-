"""Tests for the CSF ground filter plugin."""

from __future__ import annotations

import numpy as np
import pytest

from pccm.algorithms.base import RunContext
from pccm.core.document import Document


@pytest.fixture()
def ground_cloud():
    """A point cloud with a flat ground plane at z=0 and raised objects."""
    import open3d as o3d

    rng = np.random.default_rng(42)
    ground_pts = rng.random((500, 3))
    ground_pts[:, 2] = rng.random(500) * 0.1  # thin band near z=0
    object_pts = rng.random((100, 3))
    object_pts[:, 2] += 2.0  # elevated
    all_pts = np.vstack([ground_pts, object_pts])
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(all_pts)
    return pcd


class TestCSFGroundFilter:
    def test_labels_ground(self, ground_cloud):
        from pccm.plugins.matlab.ground_filter_csf.algorithm import GroundFilterCSF

        doc = Document()
        ent = doc.add_cloud(ground_cloud, "test_ground")
        ctx = RunContext(document=doc, selected_ids=[ent.id], progress=lambda *a: None, logger=None)
        result = GroundFilterCSF().run(ctx, source=ent.id, threshold=0.5, iterations=500, cloth_resolution=0.5, rigidness=1)
        sf = result.scalar_field
        assert sf is not None
        labels = sf.values
        # Most of the 500 ground points should be labelled as ground (1)
        ground_count = int(labels[:500].sum())
        assert ground_count > 300, f"Expected >300 ground labels, got {ground_count}"

    def test_empty_cloud(self):
        from pccm.plugins.matlab.ground_filter_csf.algorithm import GroundFilterCSF

        import open3d as o3d

        empty_pcd = o3d.geometry.PointCloud()
        doc = Document()
        ent = doc.add_cloud(empty_pcd, "empty")
        ctx = RunContext(document=doc, selected_ids=[ent.id], progress=lambda *a: None, logger=None)
        result = GroundFilterCSF().run(ctx, source=ent.id, threshold=0.5, iterations=500, cloth_resolution=0.5, rigidness=1)
        assert len(result.scalar_field.values) == 0
