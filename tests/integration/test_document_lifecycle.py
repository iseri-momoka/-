"""Integration tests: end-to-end Document + algorithm + view flow."""

from __future__ import annotations

import numpy as np
import pytest

from pccm.algorithms.base import RunContext
from pccm.algorithms.filter.voxel import VoxelDownsample
from pccm.core.document import Document


def _make_pcd(n=500, seed=42):
    import open3d as o3d

    rng = np.random.default_rng(seed)
    pts = rng.random((n, 3)) * 5.0
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    return pcd


def test_load_apply_undo_redo():
    doc = Document()
    pcd = _make_pcd(500)
    ent = doc.add_cloud(pcd, "raw")

    ctx = RunContext(document=doc, selected_ids=[ent.id], progress=lambda *a: None, logger=None)
    result = VoxelDownsample().run(ctx, source=ent.id, voxel_size=0.5)
    new_id = doc.add_entity(result.entities[0])

    # Now undo: should remove the new entity
    doc.undo()
    assert new_id not in doc.entities

    # Redo: re-added
    doc.redo()
    assert new_id in doc.entities


def test_signals_fire_on_addition():
    from pccm.core.signals import bus, ENTITY_ADDED

    doc = Document()
    fired = []

    def handler(sender, **kw):
        fired.append(kw.get("entity_id"))

    bus.connect(ENTITY_ADDED, handler)
    pcd = _make_pcd(50)
    ent = doc.add_cloud(pcd, "signaled")
    assert ent.id in fired
