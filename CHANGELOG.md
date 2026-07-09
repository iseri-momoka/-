# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project skeleton: directory structure, pyproject.toml, CI/CD, pre-commit.
- Core module: `Document`, `Entity`, `History` (command pattern), `blinker` event bus.
- Algorithms: `Algorithm` protocol, `AlgorithmRegistry`, `ParamSpec` contract.
- I/O: format registry with stub readers for LAS, PLY, PCD, OBJ, E57.
- GUI: `Open3DWidget` (offscreen blit bridge), `ViewerService`, `MainWindow`.
- Plugin system: `PluginManager`, `plugins.api` curated surface, TOML manifest.
- MATLAB port scaffold: `tools/matlab_to_python/template_algorithm.py`.
- Pre-commit hooks: ruff, mypy, import-linter, trailing-whitespace.
- GitHub Actions CI: lint + test on Linux/Windows/macOS.

## [0.1.0] — Unreleased

- Project skeleton with build tooling (see above).
