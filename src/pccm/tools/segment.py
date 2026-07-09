"""Segmentation tool: extract a subset of points as a new cloud."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import open3d as o3d

from pccm.core.types import Entity, EntityKind


def extract_by_mask(
    cloud: "o3d.geometry.PointCloud", mask: np.ndarray
) -> Entity:
    """Create a new entity from points where *mask* is True.

    Parameters
    ----------
    cloud : open3d.geometry.PointCloud
    mask : np.ndarray
        Boolean array of length ``len(cloud.points)``.

    Returns
    -------
    Entity
        A new cloud entity containing only the selected points.
    """
    import open3d as o3d

    points = np.asarray(cloud.points)
    indices = np.where(mask)[0].tolist()
    subset = cloud.select_by_index(indices)
    return Entity(
        name="Segment",
        kind=EntityKind.CLOUD,
        data=subset,
    )


def extract_by_indices(
    cloud: "o3d.geometry.PointCloud", indices: list[int]
) -> Entity:
    """Create a new entity from an explicit list of point indices."""
    subset = cloud.select_by_index(indices)
    return Entity(
        name="Segment",
        kind=EntityKind.CLOUD,
        data=subset,
    )
