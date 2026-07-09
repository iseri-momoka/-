# PCCM Architecture Guide

## Overview

PCCM (Point Cloud Compare & Manage) is a Python desktop application for
3D point cloud processing, inspired by CloudCompare.  It uses **PySide6**
for the GUI and **open3d** for 3D data processing.

---

## Layer Architecture

```
┌──────────────────────────────────────────────┐
│              PySide6 GUI Layer               │
│  main_window · viewer · panels · dialogs ·  │
│  actions · resources                         │
└──────────┬───────────────────────────────────┘
           │  imports only
┌──────────v───────────────────────────────────┐
│               Core Layer                     │
│  Document · Entity · History · signals       │
│  (NO PySide6 imports allowed)               │
└──────────┬───────────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───v─────┐ ┌────v────┐
│  I/O    │ │ Algorithms│
│ (open3d │ │ (open3d  │
│  laspy) │ │  numpy)  │
└─────────┘ └─────────┘
    │             │
    └──────┬──────┘
           │
┌──────────v───────────────────────────────────┐
│            Plugin Layer                      │
│  plugins.matlab.* · user_plugins/            │
│  (NO PySide6 imports allowed)               │
└──────────────────────────────────────────────┘
```

**Rule**: only `pccm.gui.*` may import PySide6.  This is enforced by
`import-linter` at CI and pre-commit time.

---

## Key Classes

### Document (`core/document.py`)

The single source of truth for all loaded entities.  Implements an
undo/redo command pattern.

```python
doc = Document()
ent = doc.add_cloud(pcd, "scan_01")
doc.delete([ent.id])
doc.undo()  # ent is back
```

### Entity (`core/types.py`)

A data container holding either a `PointCloud`, `TriangleMesh`, or
a list of child entities (group).

### AlgorithmRegistry (`algorithms/registry.py`)

Central lookup for all registered algorithms.  Algorithms self-register
at import time; the GUI reads the registry to build menus.

### ViewerService (`gui/viewer/scene.py`)

Subscribes to Document signals and mirrors changes to `Open3DWidget`.

### Open3DWidget (`gui/viewer/o3d_widget.py`)

Offscreen FBO + blit bridge from open3d to Qt.  Renders at ~60 fps.

### PluginManager (`plugins/__init__.py`)

Discovers plugins from multiple directories, loads them via importlib,
and registers their algorithms.

---

## Data Flow: Running an Algorithm

1. User selects entities in DB Tree → `Document.set_selection({ids})`
2. User picks algorithm from menu → opens `ParamDialog` (auto-built from `ParamSpec`)
3. Dialog submits → `RunContext` built with document, selected ids, progress callback
4. `Algorithm.run(ctx, **params)` → returns `AlgorithmResult`
5. Result entities added to Document → signals fire → ViewerService syncs widget

---

## File Layout

```
src/pccm/
├── core/          # Document, History, signals, types, errors
├── algorithms/    # Algorithm base classes, registry, all algorithms
├── io/            # PLY, PCD, LAS, E57, OBJ readers/writers
├── spatial/       # KDTree, Octree wrappers
├── tools/         # Selection, crop, cross-section, measure
├── gui/           # PySide6 UI — only layer with Qt imports
│   ├── viewer/    # Open3DWidget, CameraPreset, ViewerService, overlay
│   ├── panels/    # DB Tree, Properties, Histogram, Python Console
│   ├── dialogs/   # build_param_dialog, filter/registration/distance dialogs
│   ├── actions/   # File, Edit, View menu actions
│   └── resources/ # QSS styles, icons
├── plugins/       # Plugin system + built-in MATLAB ports
│   ├── api.py     # Plugin import contract
│   └── matlab/    # MATLAB-ported algorithms
└── utils/         # Logging, progress, color maps, units
```

---

## Dependency Rules

| Source layer | Allowed targets |
|---|---|
| `core` | stdlib, numpy, blinker |
| `algorithms` | core, open3d, numpy, scipy, sklearn |
| `io` | core, open3d, laspy, pye57, plyfile |
| `spatial` | core, open3d |
| `tools` | core, open3d, numpy, shapely |
| `plugins` | algorithms, core, open3d, numpy, scipy |
| `gui` | ALL of the above + PySide6, matplotlib |

Enforced by `import-linter` contracts in `importlinter.ini`.
