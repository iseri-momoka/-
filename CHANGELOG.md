# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CloudCompare C++ 前端源码集成（`原软件代码/CloudCompare-master/`）
- CMake 构建配置：Qt 6.8.0 + MSVC 2022 + OpenMP
- 15 个 git 子模块初始化（CCCoreLib、MeshIO、PoissonRecon 等）
- CloudCompare 编译成功（Release x64）：
  - `CloudCompare.exe`（主程序）
  - `ccViewer.exe`（轻量查看器）
  - `CCCoreLib.dll`、`QCC_DB_LIB.dll`、`QCC_GL_LIB.dll`、`QCC_IO_LIB.dll`、`CCAppCommon.dll`
  - `QCORE_IO_PLUGIN.dll`（核心 I/O 插件）
- `CLAUDE.md` 协作指南（构建环境、约束、目录速查）
- `docs/cloudcompare_frontend_analysis.md`（80+ 头文件分析、功能→代码映射）
- `docs/matlab_port_workflow.md`（7 步 MATLAB→Python 迁移流程）
- `src/pccm/cli/` — Python CLI 接口模块（CloudCompare ↔ Python 算法桥）
  - `cli/dispatcher.py` — 命令解析、算法调度、文件 I/O
  - `cli/formatter.py` — JSON/文本结果格式化
  - 支持 `list`/`info`/`run`/`version` 命令
- `docs/priority.md` — 模块优先级表 + 里程碑
- `docs/api_reference.md` — 各模块接口规范
- `docs/development_guide.md` — 开发规范（代码风格、Git、测试、文档）

### Changed
- README.md 重写：反映方案A 架构（C++ 前端 + Python 后端）
- `.gitignore` 更新：排除 CloudCompare build 目录、DLL/LIB 编译产物
- `__main__.py` 更新：支持 `python -m pccm cli` 模式进入 CLI

## [0.1.0] — Unreleased

- Project skeleton with build tooling (see above).
