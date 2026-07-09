"""Tests for tools — crop, measure, cross-section."""

from __future__ import annotations

import numpy as np
import pytest


class TestCropTool:
    def test_crop_aabb(self):
        from pccm.tools.crop import CropTool
        import open3d as o3d

        pts = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2], [5, 5, 5]], dtype=float)
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pts)
        result = CropTool.crop_aabb(pcd, min_bound=[-1, -1, -1], max_bound=[1.5, 1.5, 1.5])
        assert len(result.points) == 3  # first 3 inside, last outside


class TestMeasureTool:
    def test_distance(self):
        from pccm.tools.measure import MeasureTool

        d = MeasureTool.distance(np.array([0, 0, 0]), np.array([3, 4, 0]))
        np.testing.assert_allclose(d, 5.0)

    def test_triangle_area(self):
        from pccm.tools.measure import MeasureTool

        area = MeasureTool.triangle_area(
            np.array([0, 0, 0]),
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
        )
        np.testing.assert_allclose(area, 0.5)


class TestCrossSection:
    def test_extract(self):
        from pccm.tools.cross_section import CrossSectionTool
        import open3d as o3d

        pts = np.array([[0, 0, 0], [0, 0, 0.1], [0, 0, 1], [0, 0, 1.1]], dtype=float)
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pts)
        # Slab around z=0.1 with thickness 0.05
        result = CrossSectionTool.extract(pcd, plane_point=[0, 0, 0.1], normal=[0, 0, 1], thickness=0.05)
        assert len(result.points) == 1  # only the point at (0,0,0.1)
