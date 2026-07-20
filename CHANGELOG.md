# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CHANGELOG.md to track version history
- .clang-format for code formatting
- .editorconfig for editor configuration
- .gitattributes for consistent line endings
- Debug CMake preset
- Multithreaded compilation (MP_BUILD) enabled by default
- Link Time Optimization (LTO) for Release builds

### Changed
- Updated README.md with comprehensive build instructions
- Improved code readability in ccviewer.cpp
- Modernized C++ style (nullptr instead of NULL)
- Added [[nodiscard]] attributes to const getter methods
- Fixed duplicate comment blocks

## [1.38.0] - 2024

### Added
- Initial release of ccViewer SLIM
- Core point cloud viewing capabilities
- File I/O support (LAS, LAZ, TXT, XYZ, PLY, OBJ, STL, etc.)
- Point cloud processing:
  - Normal computation
  - Subsampling
  - Filter by scalar value
  - SOR outlier filter
- Tools menu:
  - Clip by Box
  - TLS plane fitting (Python script)
  - Point-to-plane projection (Python script)
  - KNN search (Python script)
  - Rotation matrix calculation (Python script)
- Plugin system (GL filters, I/O plugins, standard plugins)
- 3D mouse support
- Stereo mode support

### Dependencies
- Qt 6.x
- CCCoreLib
- Python 3.x (for script features)
- CMake 3.10+
