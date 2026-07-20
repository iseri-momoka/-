# CloudCompare Light Viewer - SLIM (MSVC Build)

## Overview
Lightweight point cloud viewer based on CloudCompare, built with MSVC.

## Features

- **File Operations**: Open/Save multiple point cloud formats (LAS, LAZ, TXT, XYZ, PLY, OBJ, STL, etc.)
- **Point Cloud Processing**:
  - Normal Computation
  - Subsampling
  - Filter by Scalar Value
  - SOR Outlier Filter
- **Tools Menu**:
  - Clip by Box
  - TLS Plane Fitting (Python script)
  - Point-to-Plane Projection (Python script)
  - KNN Search (Python script)
  - Rotation Matrix Calculation (Python script)

## Requirements

- Windows 10/11
- MSVC Compiler
- Qt 6.x
- Python 3.x (for Python script features)

## Building

1. Open the solution in Visual Studio
2. Configure Qt paths
3. Build the solution

## Directory Structure

```
.
├── ccviewer.h          # Main window header
├── ccviewer.cpp        # Main window implementation
├── python/             # Python scripts for computation
│   ├── knn_search.py
│   ├── point_projection.py
│   ├── rotation_matrix.py
│   └── tls_plane.py
└── ...
```
