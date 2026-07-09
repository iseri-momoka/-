"""Tests for Document and History command pattern."""

from __future__ import annotations

import numpy as np
import pytest

from pccm.core.document import Document
from pccm.core.types import EntityKind


@pytest.fixture()
def doc():
    return Document()


def _make_pcd(n: int = 100):
    import open3d as o3d

    pts = np.random.default_rng(0).random((n, 3))
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    return pcd


class TestDocumentAddRemove:
    def test_add_cloud(self, doc):
        pcd = _make_pcd(50)
        ent = doc.add_cloud(pcd, "cloud_a")
        assert ent.kind == EntityKind.CLOUD
        assert ent.name == "cloud_a"
        assert len(doc.entities) == 1

    def test_add_mesh(self, doc):
        import open3d as o3d

        mesh = o3d.geometry.TriangleMesh.create_sphere(radius=1.0)
        ent = doc.add_mesh(mesh, "sphere")
        assert ent.kind == EntityKind.MESH

    def test_delete_entity(self, doc):
        ent = doc.add_cloud(_make_pcd(), "del_me")
        doc.delete([ent.id])
        assert len(doc.entities) == 0

    def test_set_selection(self, doc):
        e1 = doc.add_cloud(_make_pcd(), "a")
        e2 = doc.add_cloud(_make_pcd(), "b")
        doc.set_selection({e1.id, e2.id})
        assert doc.selection == {e1.id, e2.id}


class TestHistory:
    def test_undo_redo(self, doc):
        ent = doc.add_cloud(_make_pcd(), "undo_me")
        assert doc.history.can_undo
        doc.undo()
        assert len(doc.entities) == 0
        assert doc.history.can_redo
        doc.redo()
        assert len(doc.entities) == 1

    def test_delete_undo(self, doc):
        ent = doc.add_cloud(_make_pcd(), "x")
        doc.delete([ent.id])
        assert len(doc.entities) == 0
        doc.undo()
        assert len(doc.entities) == 1

    def test_replace_undo(self, doc):
        ent = doc.add_cloud(_make_pcd(50), "orig")
        doc.replace(ent.id, _make_pcd(30), label="downsampled")
        assert len(doc.get(ent.id).data.points) == 30
        doc.undo()
        assert len(doc.get(ent.id).data.points) == 50
