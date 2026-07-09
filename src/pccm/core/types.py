"""Core data types for point cloud entities.

All concrete entity data flows through this module so that the Document
model and the algorithm layer share a single vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import numpy as np

if TYPE_CHECKING:
    import open3d as o3d


class EntityKind(Enum):
    """Discriminator for entity data."""

    CLOUD = auto()
    MESH = auto()
    GROUP = auto()
    ANNOTATION = auto()


class Unit(Enum):
    """Measurement units used for display and distance calculations."""

    METERS = "m"
    FEET = "ft"
    INCHES = "in"
    MILLIMETERS = "mm"
    CENTIMETERS = "cm"


@dataclass
class ScalarField:
    """A per-point scalar attribute that can be visualized as a color map."""

    name: str
    values: np.ndarray  # (N,) float
    colormap: str = "viridis"
    range: tuple[float, float] | None = None  # (min, max) for display

    def __post_init__(self) -> None:
        if self.values.ndim != 1:
            raise ValueError(
                f"ScalarField values must be 1-D, got {self.values.ndim}-D"
            )
        if self.range is None:
            self.range = (float(self.values.min()), float(self.values.max()))


@dataclass
class Entity:
    """A single object in the document tree (cloud, mesh, group, etc.).

    Parameters
    ----------
    id : str
        Unique identifier (uuid4).
    name : str
        Human-readable label shown in the DB tree.
    kind : EntityKind
        Discriminator for ``data``.
    data :
        The geometry data: ``open3d.geometry.PointCloud``,
        ``open3d.geometry.TriangleMesh``, or ``list[Entity]`` for groups.
    parent : Entity | None
        Back-reference to parent group, if any.
    visible : bool
        Whether the entity is currently displayed in the viewer.
    color : tuple[float, float, float]
        Override RGB in [0, 1].
    scalar_field : ScalarField | None
        Attached scalar field, if any.
    transform : np.ndarray
        4×4 affine transform.
    annotations : dict[str, Any]
        Free-form metadata (source file path, units, etc.).
    """

    name: str
    kind: EntityKind
    data: Any  # open3d.geometry.PointCloud | TriangleMesh | list[Entity]
    id: str = field(default_factory=lambda: uuid4().hex)
    parent: Entity | None = None
    visible: bool = True
    color: tuple[float, float, float] = (0.7, 0.7, 0.7)
    scalar_field: ScalarField | None = None
    transform: np.ndarray = field(
        default_factory=lambda: np.eye(4, dtype=np.float64)
    )
    annotations: dict[str, Any] = field(default_factory=dict)

    # Convenience helpers -------------------------------------------------

    @property
    def is_group(self) -> bool:
        return self.kind == EntityKind.GROUP

    @property
    def children(self) -> list[Entity]:
        """Direct children (only meaningful for groups)."""
        if self.kind != EntityKind.GROUP or not isinstance(self.data, list):
            return []
        return self.data

    def point_count(self) -> int | None:
        """Return the number of points, or ``None`` if not a cloud."""
        if self.kind == EntityKind.CLOUD:
            import open3d as o3d

            if isinstance(self.data, o3d.geometry.PointCloud):
                return len(self.data.points)
        return None
