"""Generate a PCCM plugin skeleton from a MATLAB function header.

Usage::

    python tools/matlab_to_python/template_algorithm.py <algorithm_name>

Produces the directory structure under ``src/pccm/plugins/matlab/<name>/``
and a test file under ``tests/unit/plugins/matlab/test_<name>.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def create_plugin(name: str) -> None:
    pkg_dir = PROJECT_ROOT / "src" / "pccm" / "plugins" / "matlab" / name
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # __init__.py
    (pkg_dir / "__init__.py").write_text(f'"""MATLAB port: {name}."""\n')

    # algorithm.py
    algo_py = f'''\
"""MATLAB port: {name}."""

from __future__ import annotations

import numpy as np

from pccm.algorithms.base import (
    AlgorithmBase,
    AlgorithmResult,
    ParamSpec,
    ParamType,
    RunContext,
)
from pccm.plugins.api import register

PARAMS = (
    ParamSpec("source", "Source cloud", ParamType.POINT_CLOUD_REF, default=""),
    # TODO: add algorithm-specific params here
)


class Algorithm(AlgorithmBase):
    id = "matlab.{name}"
    name = "{name} (MATLAB port)"
    category = "Plugins / MATLAB"
    params = PARAMS

    def run(self, ctx: RunContext, **values) -> AlgorithmResult:
        entity = ctx.document.get(values["source"])
        if entity is None:
            raise ValueError(f"Entity not found: {{values['source']}}")
        points = np.asarray(entity.data.points)
        # TODO: implement algorithm here
        raise NotImplementedError("Port not yet implemented")


register(Algorithm())
'''
    (pkg_dir / "algorithm.py").write_text(algo_py)

    # plugin.toml
    (pkg_dir / "plugin.toml").write_text(f"""\
[plugin]
name = "{name}"
version = "0.1.0"
entry = "pccm.plugins.matlab.{name}.algorithm"
author = ""
description = ""
license = "GPL-3.0"
""")

    # Test file
    test_dir = PROJECT_ROOT / "tests" / "unit" / "plugins" / "matlab"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_py = f'''\
"""Tests for the MATLAB port: {name}."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="TODO: implement port")
class Test{name.title().replace("_", "")}:
    def test_runs(self):
        pass
'''
    (test_dir / f"test_{name}.py").write_text(test_py)

    # Reference directory
    ref_dir = pkg_dir / "reference"
    ref_dir.mkdir(parents=True, exist_ok=True)

    print(f"Created plugin skeleton: {pkg_dir}")
    print(f"Test file:              {test_dir / f'test_{name}.py'}")
    print(f"Reference dir:          {ref_dir}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: template_algorithm.py <algorithm_name>", file=sys.stderr)
        return 1
    create_plugin(sys.argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
