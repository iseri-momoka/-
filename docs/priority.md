# PCCM 优先级表

> 开发团队参考：每个模块的优先级、预估工时、负责团队、依赖关系。

## 模块优先级总览

| 优先级 | 模块 | 状态 | 预估工时 | 负责团队 | 依赖 |
|:---:|---|:---:|:---:|:---:|---|
| **P0** | `core/` — Document/History/Signals | ✅ 完成 | 1 周 | @team-core | — |
| **P0** | `algorithms/` — base + registry | ✅ 完成 | 1 周 | @team-algorithms | core |
| **P0** | `io/` — LAS/PLY/PCD 读写 | ✅ 完成 | 1 周 | @team-io | core |
| **P0** | CloudCompare C++ 前端编译 | ✅ 完成 | 2 周 | @team-frontend | — |
| **P0** | `cli/` — Python CLI 接口 | ✅ 完成 | 0.5 周 | @team-algorithms | algorithms, io |
| **P1** | `algorithms/filter/` — Voxel/SOR/ROR | 🔲 待开发 | 1 周 | @team-algorithms | base, registry |
| **P1** | `gui/` — MainWindow + Viewer | 🔲 待开发 | 3 周 | @team-gui | core, io, algorithms |
| **P1** | `gui/viewer/o3d_widget.py` — 3D 视图桥 | 🔲 待开发 | 2 周 | @team-gui | open3d, PySide6 |
| **P1** | `gui/panels/` — DB树/属性面板 | 🔲 待开发 | 1 周 | @team-gui | core |
| **P2** | `algorithms/geometry/` — 法向量/曲率/RANSAC/DBSCAN | 🔲 待开发 | 2 周 | @team-algorithms | base |
| **P2** | `algorithms/registration/` — ICP/FPFH | 🔲 待开发 | 2 周 | @team-algorithms | base |
| **P2** | `algorithms/distance/` — C2C/C2M | 🔲 待开发 | 1.5 周 | @team-algorithms | base |
| **P2** | `spatial/` — KDTree/Octree | 🔲 待开发 | 0.5 周 | @team-algorithms | open3d |
| **P3** | `algorithms/mesh/` — Poisson/Decimate | 🔲 待开发 | 1.5 周 | @team-algorithms | base |
| **P3** | `tools/` — 选择/裁剪/剖面/量测 | 🔲 待开发 | 2 周 | @team-algorithms | core, algorithms |
| **P3** | `plugins/matlab/` — CSF + 更多移植 | 🔲 待开发 | 持续 | @team-matlab-port | plugins.api |
| **P3** | `gui/dialogs/` — 算法对话框 | 🔲 待开发 | 1 周 | @team-gui | algorithms, gui |
| **P4** | `gui/panels/histogram.py` — 标量场直方图 | 🔲 待开发 | 0.5 周 | @team-gui | matplotlib |
| **P4** | `gui/panels/python_console.py` — Python 控制台 | 🔲 待开发 | 0.5 周 | @team-gui | qtconsole |
| **P4** | 打包 — PyInstaller + CI/CD | 🔲 待开发 | 1 周 | @team-leads | 全部 |
| **P4** | 文档 — 用户手册 + 插件指南 | 🔲 待开发 | 1 周 | @team-leads | — |

## 依赖关系图

```
P0 (基础层)
  core/ ─────────────────────────┐
  algorithms/base + registry ────┤
  io/ ───────────────────────────┤
  cli/ ──────────────────────────┤
  CloudCompare C++ ──────────────┤
                                 │
P1 (MVP 层)                      │
  algorithms/filter/ ◄───────────┤
  gui/MainWindow ◄───────────────┘
  gui/viewer/o3d_widget
  gui/panels/db_tree + properties

P2 (算法扩展层)
  algorithms/geometry/ ◄── base
  algorithms/registration/ ◄── base
  algorithms/distance/ ◄── base
  spatial/ ◄── open3d

P3 (工具层)
  algorithms/mesh/ ◄── base
  tools/ ◄── core, algorithms
  plugins/matlab/ ◄── plugins.api
  gui/dialogs/ ◄── algorithms

P4 (完善层)
  gui/panels/histogram + python_console
  PyInstaller 打包
  文档
```

## 里程碑

| 里程碑 | 包含模块 | 目标日期 | 状态 |
|:---:|---|:---:|:---:|
| **M0** 骨架 | core, algorithms, io, cli, 配置 | 2026-07 | ✅ 完成 |
| **M1 前端** | CloudCompare 编译 | 2026-07 | ✅ 完成 |
| **M1 后端** | filter, gui 主窗口, viewer, panels | 2026-08 | 🚧 |
| **M2** | geometry, registration, distance, spatial | 2026-09 | 📋 |
| **M3** | mesh, tools, plugins, 对话框 | 2026-10 | 📋 |
| **M4** | 打包, 文档, 打磨 | 2026-11 | 📋 |

## 新人入门建议

1. **先读** `CLAUDE.md` — 了解项目约束和构建环境
2. **再读** `docs/architecture.md` — 完整架构设计
3. **选一个 P1 模块**开始：
   - Python 后端 → `algorithms/filter/` (最简单的算法)
   - GUI → `gui/viewer/o3d_widget.py` (最难的集成点)
   - C++ 前端 → `原软件代码/CloudCompare-master/qCC/` (参考分析文档)
4. **运行测试**：`pytest -m "not gui" -v`
5. **提交 PR**：遵循 `CODEOWNERS` + DoD 检查清单（见 README §8）
