"""Measurement tool: distances, angles, areas, volumes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import open3d as o3d


@dataclass
class MeasurementResult:
    """Result of a measurement operation."""

    value: float
    unit: str
    label: str
    points: list[tuple[float, float, float]]

    def __str__(self) -> str:
        return f"{self.label}: {self.value:.6f} {self.unit}"


class MeasureTool:
    """Geometric measurement utilities."""

    @staticmethod
    def distance(p1: np.ndarray, p2: np.ndarray, unit: str = "m") -> MeasurementResult:
        """Euclidean distance between two 3D points."""
        p1 = np.asarray(p1, dtype=np.float64)
        p2 = np.asarray(p2, dtype=np.float64)
        d = float(np.linalg.norm(p2 - p1))
        return MeasurementResult(
            value=d,
            unit=unit,
            label="Distance",
            points=[tuple(p1), tuple(p2)],
        )

    @staticmethod
    def angle(
        p1: np.ndarray, p_vertex: np.ndarray, p2: np.ndarray, unit: str = "deg"
    ) -> MeasurementResult:
        """Angle at *p_vertex* between the rays p_vertex→p1 and p_vertex→p2."""
        v1 = np.asarray(p1, dtype=np.float64) - np.asarray(p_vertex, dtype=np.float64)
        v2 = np.asarray(p2, dtype=np.float64) - np.asarray(p_vertex, dtype=np.float64)
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle_rad = float(np.arccos(cos_angle))
        if unit == "deg":
            value = float(np.degrees(angle_rad))
        else:
            value = angle_rad
        return MeasurementResult(
            value=value,
            unit=unit,
            label="Angle",
            points=[tuple(p1), tuple(p_vertex), tuple(p2)],
        )

    @staticmethod
    def triangle_area(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, unit: str = "m²") -> MeasurementResult:
        """Area of the triangle defined by three points."""
        v1 = np.asarray(p2, dtype=np.float64) - np.asarray(p1, dtype=np.float64)
        v2 = np.asarray(p3, dtype=np.float64) - np.asarray(p1, dtype=np.float64)
        area = 0.5 * float(np.linalg.norm(np.cross(v1, v2)))
        return MeasurementResult(
            value=area,
            unit=unit,
            label="Triangle Area",
            points=[tuple(p1), tuple(p2), tuple(p3)],
        )

    @staticmethod
    def mesh_volume(mesh: "o3d.geometry.TriangleMesh", unit: str = "m³") -> MeasurementResult:
        """Signed volume of a closed triangle mesh."""
        volume = mesh.get_volume()
        return MeasurementResult(
            value=float(volume),
            unit=unit,
            label="Mesh Volume",
            points=[],
        )

    @staticmethod
    def mesh_surface_area(mesh: "o3d.geometry.TriangleMesh", unit: str = "m²") -> MeasurementResult:
        """Surface area of a triangle mesh."""
        area = mesh.get_surface_area()
        return MeasurementResult(
            value=float(area),
            unit=unit,
            label="Surface Area",
            points=[],
        )
