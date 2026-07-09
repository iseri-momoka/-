# Plugin Author Guide

## Quick Start

A PCCM plugin is a Python package that registers one or more `Algorithm`
instances with the global `AlgorithmRegistry` at import time.

### Minimal example

```python
# pccm_plugins_my_filter/algorithm.py
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
    ParamSpec("radius", "Radius", ParamType.FLOAT, default=0.1, min=0.0, max=10.0),
)


class MyFilter(AlgorithmBase):
    id = "my_pkg.my_filter"
    name = "My Custom Filter"
    category = "Plugins / My Category"
    params = PARAMS

    def run(self, ctx: RunContext, **values) -> AlgorithmResult:
        pcd = ctx.document.get(values["source"]).data
        # ... do something ...
        return AlgorithmResult(
            entities=[],          # create new entities if needed
            scalar_field=None,    # or attach a scalar field
            transform=None,       # or return a 4x4 transform
            diagnostics={"key": "value"},
            display_name="my_filter",
        )


register(MyFilter())
```

### Plugin manifest

```toml
# pccm_plugins_my_filter/plugin.toml
[plugin]
name = "my_filter"
version = "0.1.0"
entry = "pccm_plugins_my_filter.algorithm"
author = "Jane Doe"
description = "An example filter"
license = "MIT"
```

### Discovery paths

The `PluginManager` looks for plugins in:

1. `pccm.plugins.matlab.*`  (built-in)
2. `<user-config-dir>/pccm/plugins/`
3. `<project-root>/plugins/`

For local development, copy the plugin folder into `src/pccm/plugins/`
or into a `<project>/plugins/` directory.

---

## What plugins can import

Plugins get a controlled namespace from `pccm.plugins.api`:

- Algorithm base classes (`Algorithm`, `AlgorithmBase`, `ParamSpec`, etc.)
- `ScalarField`, `Entity` (from core)
- `numpy`, `open3d`, `scipy`, `sklearn`, `matplotlib` (if installed)
- `register()` / `register_all()` helpers

Plugins **must not** import from `pccm.gui.*` or `PySide6`.  This is
enforced by `import-linter`.

---

## Algorithm lifecycle

1. Plugin module imported → `register(MyAlgorithm())` called
2. User opens algorithm via menu → `ParamDialog` is auto-built from `params`
3. On OK → `RunContext` constructed → `Algorithm.run(ctx, **values)` called
4. Returned `AlgorithmResult` is consumed by the caller (Document, viewer, etc.)

---

## Algorithm Result

```python
@dataclass
class AlgorithmResult:
    entities: list[Entity]         # new entities to add to the Document
    scalar_field: ScalarField | None  # to attach to source entity
    transform: np.ndarray | None   # 4x4 rigid transform (for registration)
    diagnostics: dict[str, Any]    # for logging / user feedback
    display_name: str              # UI label
```

---

## Testing plugins

```python
def test_my_filter_runs():
    from pccm.algorithms.base import RunContext
    from pccm.core.document import Document
    import open3d as o3d
    import numpy as np

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.random.random((100, 3)))

    doc = Document()
    ent = doc.add_cloud(pcd, "x")
    ctx = RunContext(document=doc, selected_ids=[ent.id],
                    progress=lambda *a: None, logger=None)
    result = MyFilter().run(ctx, source=ent.id, radius=0.1)
    assert result.diagnostics.get("key") == "value"
```

---

## Tips

- Use `AlgorithmBase` (not the raw `Algorithm` Protocol) for convenience.
- Always set `id` to a unique, namespaced string (e.g. `"my_pkg.my_filter"`).
- Keep `category` consistent so the menu structure stays clean.
- Make algorithms **idempotent** when reasonable: same input → same output.
- For numerical parity with reference implementations, capture a `.npy`
  reference output and `np.testing.assert_allclose` against it.
