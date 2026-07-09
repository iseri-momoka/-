"""Generate small, deterministic test fixtures for PCCM.

Run from the project root::

    python scripts/make_fixture.py

Saves fixtures to ``tests/fixtures/``.  Total size is kept < 5 MB so
the repository stays small; large fixtures live in Git LFS.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


def write_ply(path: Path, points: np.ndarray, colors: np.ndarray | None = None) -> None:
    """Write a binary little-endian PLY file."""
    n = len(points)
    has_color = colors is not None
    with path.open("wb") as f:
        header = (
            "ply\n"
            "format binary_little_endian 1.0\n"
            f"element vertex {n}\n"
            "property float x\n"
            "property float y\n"
            "property float z\n"
        )
        if has_color:
            header += "property uchar red\nproperty uchar green\nproperty uchar blue\n"
        header += "end_header\n"
        f.write(header.encode("ascii"))
        points.astype("<f4").tofile(f)
        if has_color:
            colors.astype(np.uint8).tofile(f)


def make_synthetic_5k(out: Path) -> None:
    """5000 random points in [0, 1]^3."""
    rng = np.random.default_rng(42)
    pts = rng.random((5000, 3)).astype(np.float32)
    write_ply(out / "synthetic_5k.ply", pts)


def make_synthetic_5k_rgb(out: Path) -> None:
    """5000 points with random RGB colors."""
    rng = np.random.default_rng(42)
    pts = rng.random((5000, 3)).astype(np.float32)
    cols = (rng.random((5000, 3)) * 255).astype(np.uint8)
    write_ply(out / "synthetic_5k_rgb.ply", pts, cols)


def make_plane_with_noise(out: Path) -> None:
    """A 10k-point z=0 plane + 5% Gaussian noise in z."""
    rng = np.random.default_rng(42)
    n = 10000
    xy = rng.random((n, 2)) * 10
    z = rng.normal(0, 0.05, size=(n, 1))  # 5% noise
    pts = np.hstack([xy, z]).astype(np.float32)
    write_ply(out / "plane_with_noise.ply", pts)


def make_blobs_dbscan(out: Path) -> None:
    """Three Gaussian clusters for DBSCAN testing."""
    rng = np.random.default_rng(42)
    centers = np.array([[0, 0, 0], [5, 5, 0], [0, 5, 0]], dtype=np.float32)
    pts_per = 300
    parts = [c + rng.normal(scale=0.3, size=(pts_per, 3)).astype(np.float32) for c in centers]
    pts = np.vstack(parts).astype(np.float32)
    write_ply(out / "blobs_dbscan.ply", pts)


def make_bunny_small(out: Path) -> None:
    """A small bunny-like shape — 1500 points sampled from a parametric surface."""
    u = np.linspace(0, 2 * np.pi, 60)
    v = np.linspace(0, np.pi, 30)
    uu, vv = np.meshgrid(u, v)
    r = 1.0 + 0.3 * np.cos(3 * vv)
    x = r * np.sin(vv) * np.cos(uu)
    y = r * np.sin(vv) * np.sin(uu)
    z = r * np.cos(vv) + 0.2 * np.sin(8 * uu) * np.sin(2 * vv)
    pts = np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1).astype(np.float32)
    write_ply(out / "bunny_small.ply", pts)


def main() -> int:
    out = Path(__file__).parent.parent / "tests" / "fixtures"
    out.mkdir(parents=True, exist_ok=True)
    print(f"Writing fixtures to {out}…")
    make_synthetic_5k(out)
    make_synthetic_5k_rgb(out)
    make_plane_with_noise(out)
    make_blobs_dbscan(out)
    make_bunny_small(out)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
