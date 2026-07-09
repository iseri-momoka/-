# Architecture

PCCM is organised in layers. Only `pccm.gui` may import PySide6.
See [architecture.md](architecture.md) for the full picture.

## Data Flow Summary

```
GUI  →  Document  →  Algorithm  →  AlgorithmResult  →  Document  →  ViewerService  →  Widget
```

1. User action (menu/click) → GUI
2. GUI selects entities, builds RunContext
3. Algorithm executes against Document data
4. Result entities / scalar fields added back to Document
5. Document signals fire → ViewerService syncs widget

## Why these choices

- **PySide6** — LGPL, modern, well-supported on all 3 OSes
- **open3d** — battle-tested 3D algorithms, Python API
- **blinker** — Qt-free event bus keeps core decoupled
- **command pattern** — undo/redo with rich semantics
- **plugin via importlib** — no pkg_resources deprecation, supports entry points and filesystem manifests
