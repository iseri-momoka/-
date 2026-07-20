# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CloudCompare slim build — a lightweight 3D point cloud viewer based on **ccViewer**, expanded with selected processing dialogs from the full qCC application. This is a **secondary development codebase**, not an upstream CloudCompare fork.

**Language:** C++17 | **Framework:** Qt 6 | **Build:** CMake 3.10+

## Build Commands

```bash
# Recommended: use CMake preset
cmake --preset slim

# Manual configure
mkdir build2 && cd build2
cmake .. -DCMAKE_BUILD_TYPE=Release -DPLUGIN_IO_QCORE=ON -DPLUGIN_IO_QLAS=ON \
  -DOPTION_USE_DXF_LIB=OFF -DOPTION_USE_SHAPE_LIB=OFF

# Build
cmake --build build2 --config Release --parallel
```

Qt deployment (windeployqt/macdeployqt) runs automatically via `cmake/DeployQt.cmake`.

Key CMake options: `OPTION_BUILD_CCVIEWER` (ON), `BUILD_TESTING` (OFF), `OPTION_MP_BUILD` (MSVC multithread), `OPTION_USE_VISUAL_LEAK_DETECTOR` (debug memory leak detection).

### External Dependencies

**CCCoreLib** must be cloned before building:
```bash
cd libs/qCC_db/extern
git clone --depth 1 https://github.com/CloudCompare/CCCoreLib.git
```

LASzip (optional, for LAS format) is bundled in `libs/qCC_io/extern/laszip/`.

## Architecture

### Library dependency order (`libs/`)

Built strictly in order (see `libs/CMakeLists.txt`):
**CCFbo** → **qCC_db** → **qCC_io** → **qCC_glWindow** → **CCPluginStub** → **CCPluginAPI** → **CCAppCommon**

Each is an internal shared library. `qCC_db` contains core data models (ccPointCloud, ccHObject, etc.); its `extern/CCCoreLib/` is the external computational geometry library.

### Plugin system (`plugins/`)

Plugins are built as shared libraries via `AddPlugin()` in `plugins/cmake/Plugins.cmake`. Three types: `gl` (OpenGL shaders), `io` (file formats), `standard` (generic, Python/MATLAB extension point).

Each plugin **must** include: `{foldername}.qrc` resource file and `info.json` metadata. Plugins auto-link CCCoreLib, CCPluginAPI, CCPluginStub.

Current plugins: `qCoreIO` (OBJ/STL/VTK/OFF/PTX) and `qLASIO` (LAS/LAZ/COPC).

### Main application (`ccViewer/`)

`ccViewer` inherits both `QMainWindow` and `ccMainAppInterface` (plugin interface API). Class definition in `ccviewer.h`, implementation in `ccviewer.cpp` (~41KB, heavily modified for slim features).

`main.cpp` initializes OpenGL, registers I/O filters, loads plugins, creates the main window.

### Extracted qCC code (`qCC_selected/`)

- `dialogs/` — 8 processing dialog implementations copied from qCC
- `support/` — Utility code (ccEntityAction, ccLibAlgorithms, ccRegistrationTools, ccHistogramWindow, ccEnvelopeExtractor, ccUtils)
- `db_tree/` — Database tree controls (ccDBRoot)
- `ui_templates/` — Qt .ui files for extracted dialogs

**Currently compiled into ccViewer** (4 of 8, see `ccViewer/CMakeLists.txt`):
ccNormalComputationDlg, ccSubsamplingDlg, ccFilterByValueDlg, ccSORFilterDlg

**Present but not yet wired into the build:** ccComparisonDlg, ccRegistrationDlg, ccAlignDlg, ccGraphicalSegmentationTool

### Adding a new dialog to ccViewer

1. Add `.cpp`/`.h` files from `qCC_selected/dialogs/` to `source_list`/`header_list` in `ccViewer/CMakeLists.txt`
2. Add corresponding `.ui` file to `qcc_ui_list`
3. Add menu action and slot in `ccviewer.h`/`ccviewer.cpp` (follow existing `m_action*` / `doAction*` pattern)

### Adding a new plugin

1. Create directory under `plugins/core/` with source files, `.qrc`, and `info.json`
2. In its CMakeLists.txt: `AddPlugin(NAME YourPluginName TYPE io)`
3. Add `add_subdirectory(YourPluginName)` in the parent CMakeLists

## Code Conventions

- CMake modules in `cmake/` are included by the top-level `CMakeLists.txt`
- Qt AUTOMOC and AUTORCC are enabled globally; `ccViewer/CMakeLists.txt` uses `qt6_wrap_ui()` explicitly for cross-directory UI files
- MSVC builds define `NOMINMAX`, `_CRT_SECURE_NO_WARNINGS`, `__STDC_LIMIT_MACROS`
- ccache is used automatically when available (configured in `cmake/CMakeSetCompilerOptions.cmake`)
- Use `[[nodiscard]]` for const getter methods
- Use `nullptr` instead of `NULL`
- Chinese documentation files (`CloudCompare-*-说明表.txt`) contain per-file descriptions of the original CloudCompare codebase — reference when modifying upstream code

## Python Scripts

Located in `python/` directory. These scripts are invoked via QProcess from the C++ application.

### TLS Plane Fitting (`tls_plane.py`)
Fits a plane to 3D point cloud using Total Least Squares (SVD).
- Input: CSV file (x,y,z format)
- Output: JSON with plane equation (a,b,c,d) for ax+by+cz+d=0

### Point-to-Plane Projection (`point_projection.py`)
Projects points orthogonally onto a plane.
- Input: Points CSV + plane parameters JSON
- Output: Projected points CSV

### KNN Search (`knn_search.py`)
K-Nearest Neighbors search using KDTree.
- Input: Query point CSV + points CSV + k value
- Output: JSON with nearest neighbors and distances

### Rotation Matrix (`rotation_matrix.py`)
Computes rotation matrix from normal1 to normal2 using quaternions.
- Input: Two normal vectors as JSON
- Output: 3x3 rotation matrix JSON

## Build Optimizations

The following optimizations are enabled by default:
- **MP_BUILD**: Multithreaded compilation (MSVC /MP flag)
- **LTO**: Link Time Optimization for Release builds
- **ccache**: Automatic compiler caching when available

To disable optimizations, set `OPTION_MP_BUILD=OFF` in CMake.
