"""CLI dispatcher — the bridge between CloudCompare and Python algorithms.

Reads command-line arguments, loads input files into a Document,
dispatches to the AlgorithmRegistry, and writes output files.

This module must **not** import PySide6.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

from pccm.algorithms.base import RunContext
from pccm.algorithms.registry import registry
from pccm.cli.formatter import format_result
from pccm.core.document import Document
from pccm.core.types import EntityKind

logger = logging.getLogger("pccm.cli")


# ------------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="pccm",
        description="PCCM CLI — Point Cloud Compare & Manage algorithm dispatcher",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--log-format",
        default="%(levelname)s %(name)s: %(message)s",
        help="Logging format string",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- list ---
    list_parser = sub.add_parser("list", help="List available algorithms")
    list_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    list_parser.add_argument(
        "--category",
        help="Filter by category (substring match)",
    )

    # --- info ---
    info_parser = sub.add_parser("info", help="Show algorithm parameter details")
    info_parser.add_argument("algorithm_id", help="Algorithm id (e.g. filter.voxel)")

    # --- run ---
    run_parser = sub.add_parser("run", help="Run an algorithm")
    run_parser.add_argument("algorithm_id", help="Algorithm id (e.g. filter.voxel)")
    run_parser.add_argument(
        "--input", "-i",
        action="append",
        dest="inputs",
        required=True,
        help="Input file path (can be repeated for multi-cloud algorithms)",
    )
    run_parser.add_argument(
        "--output", "-o",
        action="append",
        dest="outputs",
        help="Output file path (can be repeated)",
    )
    run_parser.add_argument(
        "--select",
        help="Comma-separated entity names/indices to select (default: all)",
    )
    run_parser.add_argument(
        "--params", "-p",
        help='Algorithm parameters as JSON string, e.g. \'{"voxel_size": 0.05}\'',
    )
    run_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files",
    )
    run_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="json",
        help="Result output format (default: json)",
    )

    # --- version ---
    sub.add_parser("version", help="Show PCCM version")

    return parser


# ------------------------------------------------------------------
# Command handlers
# ------------------------------------------------------------------


def _ensure_plugins_loaded() -> None:
    """Lazily import plugin modules to populate the registry."""
    # Import built-in MATLAB plugins
    try:
        import pccm.plugins.matlab.ground_filter_csf.algorithm  # noqa: F401
    except ImportError:
        pass  # Optional dependency — CSF may not be installed


def _load_inputs(paths: list[str]) -> Document:
    """Load input files into a fresh Document.

    Returns the document with one Entity per loaded file.
    """
    from pccm.io import load_point_cloud

    doc = Document()
    for p in paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        logger.info("Loading %s ...", path.name)
        pcd = load_point_cloud(path)
        doc.add_cloud(pcd, name=path.stem)
        logger.info("  → %d points loaded", len(pcd.points))
    return doc


def _resolve_selection(
    doc: Document,
    select_arg: str | None,
) -> list[str]:
    """Resolve the --select argument to entity ids.

    Accepts entity names or 0-based indices.
    """
    if select_arg is None:
        return list(doc.entities.keys())

    ids: list[str] = []
    entity_list = list(doc.entities.values())
    for token in select_arg.split(","):
        token = token.strip()
        # Try index first
        try:
            idx = int(token)
            if 0 <= idx < len(entity_list):
                ids.append(entity_list[idx].id)
            else:
                raise ValueError(f"Index {idx} out of range (0-{len(entity_list) - 1})")
            continue
        except ValueError as e:
            if "out of range" in str(e):
                raise
        # Try name match
        found = [eid for eid, ent in doc.entities.items() if ent.name == token]
        if found:
            ids.extend(found)
        else:
            raise ValueError(f"No entity found with name or index: {token!r}")
    return ids


def _write_output(path: str, entity: Any, overwrite: bool) -> None:
    """Write an entity's data to a file."""
    from pccm.io import save_point_cloud

    out = Path(path)
    if out.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {out}  (use --overwrite to replace)"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    save_point_cloud(out, entity.data)
    logger.info("Saved %d points → %s", len(entity.data.points), out)


# ------------------------------------------------------------------
# Public dispatch API
# ------------------------------------------------------------------


def dispatch(args: list[str] | None = None) -> int:
    """Parse *args* and execute the CLI command.

    Parameters
    ----------
    args : list[str], optional
        Command-line arguments.  Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code (0 = success, 1 = error).
    """
    parser = build_parser()
    parsed = parser.parse_args(args)

    # Configure logging
    level = logging.DEBUG if parsed.verbose else logging.INFO
    logging.basicConfig(level=level, format=parsed.log_format)

    if parsed.command is None:
        parser.print_help()
        return 0

    try:
        if parsed.command == "version":
            return _cmd_version()
        elif parsed.command == "list":
            return _cmd_list(parsed)
        elif parsed.command == "info":
            return _cmd_info(parsed)
        elif parsed.command == "run":
            return _cmd_run(parsed)
        else:
            parser.print_help()
            return 0
    except Exception as exc:
        logger.error("Error: %s", exc)
        if parsed.verbose:
            logger.exception("Traceback:")
        return 1


def _cmd_version() -> int:
    """Print PCCM version."""
    from pccm._version import __version__, APP_NAME_FULL

    print(f"{APP_NAME_FULL} (PCCM) {__version__}")
    return 0


def _cmd_list(parsed: argparse.Namespace) -> int:
    """List all registered algorithms."""
    _ensure_plugins_loaded()

    algs = registry.all_algorithms()
    if parsed.category:
        cat_lower = parsed.category.lower()
        algs = [a for a in algs if cat_lower in a.category.lower()]

    if parsed.format == "json":
        data = [
            {
                "id": a.id,
                "name": a.name,
                "category": a.category,
                "params": [
                    {"name": p.name, "type": p.type.value, "default": p.default}
                    for p in a.params
                ],
            }
            for a in algs
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        if not algs:
            print("No algorithms registered.")
            return 0
        # Group by category
        cats: dict[str, list[Any]] = {}
        for a in algs:
            cats.setdefault(a.category, []).append(a)
        for cat in sorted(cats):
            print(f"\n[{cat}]")
            for a in cats[cat]:
                params_str = ", ".join(
                    f"{p.name} ({p.type.value})" for p in a.params
                )
                print(f"  {a.id:<30s} {a.name}")
                if params_str:
                    print(f"  {'':30s} params: {params_str}")
    return 0


def _cmd_info(parsed: argparse.Namespace) -> int:
    """Show detailed info for a single algorithm."""
    _ensure_plugins_loaded()

    alg = registry.get(parsed.algorithm_id)
    if alg is None:
        print(f"Error: algorithm {parsed.algorithm_id!r} not found.", file=sys.stderr)
        print("Use 'pccm list' to see available algorithms.", file=sys.stderr)
        return 1

    info = {
        "id": alg.id,
        "name": alg.name,
        "category": alg.category,
        "params": [],
    }
    for p in alg.params:
        param_info: dict[str, Any] = {
            "name": p.name,
            "label": p.label,
            "type": p.type.value,
            "default": p.default,
        }
        if p.min is not None:
            param_info["min"] = p.min
        if p.max is not None:
            param_info["max"] = p.max
        if p.options is not None:
            param_info["options"] = list(p.options)
        if p.help:
            param_info["help"] = p.help
        info["params"].append(param_info)

    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


def _cmd_run(parsed: argparse.Namespace) -> int:
    """Run an algorithm with the given inputs and parameters."""
    _ensure_plugins_loaded()

    # 1. Look up algorithm
    alg = registry.get(parsed.algorithm_id)
    if alg is None:
        print(f"Error: algorithm {parsed.algorithm_id!r} not found.", file=sys.stderr)
        return 1

    # 2. Load inputs
    doc = _load_inputs(parsed.inputs)

    # 3. Parse parameters
    params: dict[str, Any] = {}
    if parsed.params:
        params = json.loads(parsed.params)

    # 4. Resolve selection
    selected_ids = _resolve_selection(doc, parsed.select)

    # 5. Build RunContext and run
    t0 = time.perf_counter()
    ctx = RunContext(
        document=doc,
        selected_ids=selected_ids,
        progress=lambda frac, msg: logger.info("  [%.0f%%] %s", frac * 100, msg),
        logger=logger,
    )

    result = alg.run(ctx, **params)
    elapsed = time.perf_counter() - t0

    # 6. Output results
    output_text = format_result(result, fmt=parsed.format)
    print(output_text)

    # 7. Write output files if requested
    if parsed.outputs:
        if result.entities:
            for i, out_path in enumerate(parsed.outputs):
                if i < len(result.entities):
                    _write_output(out_path, result.entities[i], parsed.overwrite)
                else:
                    logger.warning(
                        "Output path %r specified but only %d result entities",
                        out_path,
                        len(result.entities),
                    )
        else:
            # No entities in result — check if the algorithm modified the document
            # (e.g., scalar field attached to existing entity)
            logger.info("Algorithm produced no new entities (scalar field or in-place modification)")

    logger.info("Algorithm completed in %.3f s", elapsed)
    return 0


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------


def main() -> None:
    """Entry point for ``python -m pccm.cli``."""
    sys.exit(dispatch())


if __name__ == "__main__":
    main()
