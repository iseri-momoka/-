# CloudCompare slim build - 3D Point Cloud Viewer

A lightweight 3D point cloud viewer based on ccViewer, expanded with selected processing dialogs from the full qCC application.

## Features

- **Point Cloud Viewing**: Efficient 3D visualization of point clouds
- **Processing Dialogs**:
  - Normal Computation
  - Subsampling
  - Filter by Value
  - SOR Filter (Statistical Outlier Removal)
- **I/O Formats**:
  - qCoreIO: OBJ, STL, VTK, OFF, PTX
  - qLASIO: LAS, LAZ, COPC
- **Python Scripts**: TLS plane fitting, point projection, KNN search

## Requirements

- C++17 compiler
- Qt 6
- CMake 3.10+

## Build Instructions

### 1. Clone the repository



### 2. Install CCCoreLib (external dependency)



### 3. Build with CMake

-- Selecting Windows SDK version 10.0.26100.0 to target Windows 10.0.26200.
-- The C compiler identification is MSVC 19.51.36248.0
-- The CXX compiler identification is MSVC 19.51.36248.0
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: D:/vs2026/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe - skipped
-- Detecting C compile features
-- Detecting C compile features - done
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: D:/vs2026/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Configuring incomplete, errors occurred!
-- Selecting Windows SDK version 10.0.26100.0 to target Windows 10.0.26200.
-- Configuring incomplete, errors occurred!

## Project Structure

- `ccViewer/` - Main application
- `libs/` - Core libraries (CCFbo, qCC_db, qCC_io, qCC_glWindow, etc.)
- `plugins/` - I/O and processing plugins
- `qCC_selected/` - Extracted dialogs from full qCC
- `python/` - Python utility scripts

## License

See LICENSE file for details.
