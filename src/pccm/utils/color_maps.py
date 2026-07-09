"""Colour-map utilities: map scalar values → RGB arrays via matplotlib colormaps.

Used by ``algorithms.scalar_field.colorize`` and the histogram panel.
"""

from __future__ import annotations

import numpy as np


def scalar_to_rgb(
    values: np.ndarray,
    colormap_name: str = "viridis",
    vmin: float | None = None,
    vmax: float | None = None,
) -> np.ndarray:
    """Map a 1-D scalar array to an (N, 3) RGB array using *colormap_name*.

    Parameters
    ----------
    values : np.ndarray
        1-D array of scalar values.
    colormap_name : str
        Any matplotlib colormap name.
    vmin, vmax : float, optional
        Normalization bounds; defaults to ``values.min() / max()``.

    Returns
    -------
    np.ndarray
        ``(N, 3)`` float64 array in [0, 1].
    """
    import matplotlib.cm as cm

    vmin = vmin if vmin is not None else float(values.min())
    vmax = vmax if vmax is not None else float(values.max())
    if vmax <= vmin:
        vmax = vmin + 1.0
    norm = np.clip((values.astype(np.float64) - vmin) / (vmax - vmin), 0.0, 1.0)
    cmap = cm.get_cmap(colormap_name)
    rgba = cmap(norm)
    return rgba[:, :3].astype(np.float64)


# Predefined colormaps that work well with point clouds
COLORMAPS = ("viridis", "plasma", "coolwarm", "jet", "rainbow", "terrain", "RdYlBu")
