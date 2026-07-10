"""Result formatting for CLI output.

Converts :class:`~pccm.algorithms.base.AlgorithmResult` to human-readable
text or JSON for piping to CloudCompare or other tools.

This module must **not** import PySide6.
"""

from __future__ import annotations

import json
from typing import Any

from pccm.algorithms.base import AlgorithmResult


def format_result(result: AlgorithmResult, fmt: str = "json") -> str:
    """Format an AlgorithmResult as a string.

    Parameters
    ----------
    result : AlgorithmResult
        The algorithm output to format.
    fmt : str
        ``"json"`` for structured output, ``"text"`` for human-readable.

    Returns
    -------
    str
        Formatted result string.
    """
    if fmt == "json":
        return _format_json(result)
    return _format_text(result)


def _format_json(result: AlgorithmResult) -> str:
    """Format as indented JSON."""
    data: dict[str, Any] = {
        "status": "ok",
        "display_name": result.display_name or None,
    }

    # Entity summary (we don't serialize full geometry — just metadata)
    if result.entities:
        data["entities"] = []
        for ent in result.entities:
            ent_info: dict[str, Any] = {
                "name": getattr(ent, "name", "unknown"),
                "kind": getattr(ent.kind, "name", str(getattr(ent, "kind", "unknown"))),
            }
            # Try to get point/face count
            point_count = getattr(ent, "point_count", lambda: None)()
            if point_count is not None:
                ent_info["point_count"] = point_count
            data["entities"].append(ent_info)

    # Scalar field summary
    if result.scalar_field is not None:
        sf = result.scalar_field
        data["scalar_field"] = {
            "name": sf.name,
            "length": len(sf.values),
            "min": float(sf.values.min()) if len(sf.values) > 0 else None,
            "max": float(sf.values.max()) if len(sf.values) > 0 else None,
            "mean": float(sf.values.mean()) if len(sf.values) > 0 else None,
        }

    # Transform
    if result.transform is not None:
        data["transform"] = result.transform.tolist()

    # Diagnostics
    if result.diagnostics:
        data["diagnostics"] = result.diagnostics

    return json.dumps(data, indent=2, ensure_ascii=False)


def _format_text(result: AlgorithmResult) -> str:
    """Format as human-readable text."""
    lines: list[str] = []

    if result.display_name:
        lines.append(f"Algorithm: {result.display_name}")
    lines.append("")

    if result.entities:
        lines.append(f"Output entities: {len(result.entities)}")
        for ent in result.entities:
            name = getattr(ent, "name", "unknown")
            kind = getattr(ent.kind, "name", str(getattr(ent, "kind", "?")))
            count = getattr(ent, "point_count", lambda: None)()
            if count is not None:
                lines.append(f"  - {name} ({kind}, {count} points)")
            else:
                lines.append(f"  - {name} ({kind})")
    else:
        lines.append("Output entities: none")

    if result.scalar_field is not None:
        sf = result.scalar_field
        lines.append("")
        lines.append(f"Scalar field: {sf.name}")
        lines.append(f"  length: {len(sf.values)}")
        if len(sf.values) > 0:
            lines.append(f"  range: [{sf.values.min():.6f}, {sf.values.max():.6f}]")
            lines.append(f"  mean:  {sf.values.mean():.6f}")

    if result.transform is not None:
        lines.append("")
        lines.append("Transform (4×4):")
        for row in result.transform:
            lines.append("  " + " ".join(f"{v:12.6f}" for v in row))

    if result.diagnostics:
        lines.append("")
        lines.append("Diagnostics:")
        for k, v in result.diagnostics.items():
            lines.append(f"  {k}: {v}")

    return "\n".join(lines)
