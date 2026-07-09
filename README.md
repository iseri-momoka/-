# PCCM — Point Cloud Compare & Manage

> Python 桌面端 3D 点云处理软件，对标 CloudCompare，支持 MATLAB 算法以插件方式渐进式迁移到 Python。

![status](https://img.shields.io/badge/status-M0%20skeleton-blue)
![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![license](https://img.shields.io/badge/license-GPL--3.0-green)
![engine](https://img.shields.io/badge/engine-open3d-orange)
![gui](https://img.shields.io/badge/gui-PySide6-purple)

---

## 1. 项目是什么

PCCM（Point Cloud Compare & Manage）是一个**纯 Python 桌面应用**，面向点云数据的可视化、编辑、滤波、配准、距离分析、网格重建等场景。

设计目标：

- **对标 CloudCompare 的核心功能**（I/O / 可视化 / 编辑 / 滤波 / 几何 / 配准 / 距离 / 网格 / 工具）
- **算法先用 MATLAB 写，再以插件方式渐进式迁移到 Python**，不阻塞主程序演进
- **支持多人协同开发**（CI/CD、code review、模块分层）

---

## 2. 已经完成的工作

> 截止 2026-07-09，M0 骨架阶段已完成 124 个文件，覆盖全部 12 个子系统。

| # | 子系统 | 文件数 | 内容 |
|---|---|---:|---|
| 1 | 项目根配置 | 11 | `pyproject.toml`、`.gitignore`、CI、pre-commit、ruff、mypy、pytest、import-linter |
| 2 | 应用入口 | 5 | `_version.py`、`__init__`、`__main__`、`app.py`、`config.py` |
| 3 | `core/` 核心 | 6 | Document、History（命令模式）、Signals（blinker 事件总线）、Types、Errors |
| 4 | `algorithms/` 算法 | 23 | base、registry + 7 个子包（filter / geometry / registration / distance / scalar_field / mesh） |
| 5 | `io/` 文件 I/O | 7 | registry + 5 种格式（LAS/LAZ、PLY、PCD、OBJ、E57）读写 |
| 6 | `spatial/` 空间结构 | 2 | KDTree、Octree 封装 |
| 7 | `tools/` 工具 | 5 | 选择、分割、裁剪、剖面、量测 |
| 8 | `utils/` 工具 | 4 | 日志、进度、colormap、单位 |
| 9 | `gui/` 界面 | 16 | main_window、viewer、4 个 panel、model、对话框、3 个 action、QSS 样式 |
| 10 | `plugins/` 插件 | 7 | api、builtin_voxel_color、matlab/CSF（含 manifest）、README |
| 11 | CI/CD | 1 | GitHub Actions ci.yml（lint / test-linux / test-windows / test-macos / test-gui） |
| 12 | `tests/` 测试 | 9 | conftest + 8 个测试文件（unit / integration / gui） |
| 13 | `docs/` 文档 | 3 | README、architecture、plugin_author_guide |
| 14 | `scripts/` 脚本 | 2 | make_fixture、profile_viewer |
| 15 | `tools/matlab_to_python/` | 3 | 模板生成、docstring 解析、参考输出对比 |
| 16 | `pyinstaller/` 打包 | 2 | pccm.spec、hook-open3d |
| **合计** | | **~106** | + 18 个配置文件 / TOML / QSS / MD |

**第一份 MATLAB → Python 移植已完成**：`ground_filter_csf`（布料模拟滤波），含完整算法实现、单测、manifest 清单。

---

## 3. 仓库结构

```
点云软件开发/
├── pyproject.toml              # PEP 621 单包配置、依赖锁、工具配置
├── .gitignore
├── .pre-commit-config.yaml     # pre-commit 钩子（ruff + mypy + import-linter）
├── .ruff.toml
├── mypy.ini
├── importlinter.ini            # 7 条分层契约
├── pytest.ini
├── README.md                   # ← 本文件
├── LICENSE                     # GPL-3.0-or-later
├── CHANGELOG.md
├── CODEOWNERS                  # 模块所有权
│
├── .github/workflows/ci.yml    # CI：lint + 三系统测试 + GUI
│
├── docs/                       # 文档
│   ├── architecture.md
│   ├── plugin_author_guide.md
│   └── README.md
│
├── scripts/                    # 一次性脚本
│   ├── make_fixture.py
│   └── profile_viewer.py
│
├── tools/matlab_to_python/     # MATLAB→Python 迁移工具
│   ├── template_algorithm.py
│   ├── docstring_extractor.py
│   └── compare_outputs.py
│
├── tests/                      # 测试
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── gui/
│
├── src/pccm/                   # 源码（src 布局）
│   ├── __main__.py             # `python -m pccm`
│   ├── app.py                  # QApplication 启动
│   ├── config.py               # 路径配置
│   │
│   ├── core/                   # ★ 禁止 import PySide6
│   │   ├── document.py         # Document / Entity
│   │   ├── history.py          # 命令模式 undo/redo
│   │   ├── signals.py          # blinker 事件总线
│   │   ├── types.py
│   │   └── errors.py
│   │
│   ├── algorithms/             # ★ 禁止 import PySide6
│   │   ├── base.py             # Algorithm / ParamSpec / Result 协议
│   │   ├── registry.py         # AlgorithmRegistry 中央调度
│   │   ├── filter/             # 体素 / SOR / ROR / 平滑
│   │   ├── geometry/           # 法向量 / 曲率 / 密度 / RANSAC / DBSCAN
│   │   ├── registration/       # ICP / FPFH+RANSAC
│   │   ├── distance/           # C2C / C2M / M3C2
│   │   ├── scalar_field/       # compute / histogram / colorize
│   │   └── mesh/               # Poisson / decimate / hole_fill
│   │
│   ├── io/                     # ★ 禁止 import PySide6
│   │   ├── registry.py
│   │   ├── las_reader.py
│   │   ├── ply_reader.py
│   │   ├── pcd_reader.py
│   │   ├── obj_reader.py
│   │   ├── e57_reader.py
│   │   └── writers.py
│   │
│   ├── spatial/                # KDTree / Octree
│   ├── tools/                  # 选择 / 裁剪 / 剖面 / 量测
│   ├── utils/                  # 日志 / 进度 / colormap / 单位
│   │
│   ├── gui/                    # ★ PySide6 唯一入口
│   │   ├── main_window.py
│   │   ├── viewer/             # open3d ↔ Qt 桥（offscreen blit）
│   │   ├── panels/             # db_tree / properties / histogram / python_console
│   │   ├── models/             # EntityTreeModel
│   │   ├── dialogs/            # build_param_dialog（自动生成）
│   │   ├── actions/            # file / edit / view
│   │   └── resources/styles/   # default.qss
│   │
│   └── plugins/                # 插件（Qt-free）
│       ├── api.py              # 受控 re-export
│       ├── builtin_voxel_color.py
│       └── matlab/
│           ├── README.md
│           └── ground_filter_csf/   # ★ 第一个 MATLAB 移植
│
└── pyinstaller/
    ├── pccm.spec
    └── hooks/hook-open3d.py
```

---

## 4. 技术栈与版本要求

### 4.1 运行时

| 包 | 版本 | 用途 |
|---|---|---|
| Python | `>=3.11,<3.13` | 3.13 wheel 滞后 |
| numpy | `>=2.0,<3` | 算法基础 |
| scipy | `>=1.13,<2` | cKDTree、griddata |
| scikit-learn | `>=1.5,<2` | DBSCAN 兜底 |
| **open3d** | `>=0.19,<0.20` | **3D 引擎（核心）** |
| **PySide6** | `>=6.7,<6.9` | **GUI（LGPL）** |
| matplotlib | `>=3.9,<4` | 直方图面板（仅 `FigureCanvasQTAgg`） |
| laspy | `>=2.5,<3` | LAS / LAZ |
| pye57 | `>=0.4` | E57 |
| plyfile | `>=1.1` | PLY 兜底 |
| shapely | `>=2.0` | 多边形选择 |
| qtconsole | `>=5.5` | Python 控制台面板 |
| blinker | `>=1.7` | core 事件总线 |

### 4.2 开发与测试

| 包 | 版本 | 用途 |
|---|---|---|
| pytest | `>=8` | 单元/集成测试 |
| pytest-qt | `>=4.4` | GUI 测试 |
| pytest-cov | `>=5` | 覆盖率 |
| pytest-benchmark | `>=4` | 性能回归 |
| ruff | `>=0.6` | lint + format |
| mypy | `>=1.11` | 类型检查 |
| import-linter | `>=2` | 分层契约 |
| pre-commit | `>=4` | 钩子运行器 |
| pyinstaller | `>=6.10` | 打包 .exe / .dmg / .AppImage |

### 4.3 系统要求

- **Windows 10/11** / **macOS 12+** / **Ubuntu 22.04+**
- 8 GB RAM 起步，处理 50M+ 点云建议 16 GB+
- 支持 OpenGL 3.3+ 的显卡（open3d 可视化需要）
- 磁盘：开发 2 GB；open3d + PySide6 wheel 约 1.5 GB

---

## 5. 快速开始

```bash
# 1. 克隆
git clone <your-fork-url> pccm
cd pccm

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # macOS / Linux

# 3. 安装（含开发依赖）
pip install -e ".[dev]"

# 4. 安装 pre-commit 钩子
pre-commit install

# 5. 运行
python -m pccm                   # 启动 GUI
# 或
pccm                             # 通过 console_script 启动
```

### 5.1 验证安装

```bash
# lint
ruff check src tests
mypy src/pccm
lint-imports                     # import-linter 契约

# 测试（无 GUI）
pytest -m "not gui" -v

# GUI 测试（Linux 需要 xvfb）
xvfb-run pytest -m gui -v

# 全量
pytest
```

### 5.2 打包

```bash
# 生成 standalone
pyinstaller pyinstaller/pccm.spec
# 产物在 dist/pccm/
```

---

## 6. 架构核心

### 6.1 分层（import-linter 强制）

```
PySide6 GUI 层   ─── 唯一允许 import PySide6
       │  ↓ signals
   core / algorithms / io / spatial / tools
       │  ↑ 依赖
   open3d / numpy / scipy / laspy / pye57
```

- `pccm.core / algorithms / io / spatial / tools / plugins` **禁止** import `pccm.gui` 或 `PySide6`
- `pccm.algorithms / plugins` **禁止** import `open3d.visualization`（用 headless API）
- plugins.matlab 只能 import `pccm.plugins.api` 受控表面，**禁止** `pccm.gui` / `pccm.core.document` / `pccm.core.history`

### 6.2 核心数据流

```
用户操作 → QAction → QDialog（由 ParamSpec 自动生成）
       → Algorithm.run(ctx, **values)
       → open3d PointCloud / Mesh
       → Document.add_*  / replace
       → blinker signals
       → ViewerService / DBTreePanel / PropertiesPanel
       → Open3DWidget（offscreen blit 至 QLabel）
```

### 6.3 open3d ↔ Qt 桥

open3d 的 `O3DVisualizer` 不是 `QWidget`，强行嵌入会出现双事件循环。PCCM 采用：

- 离屏 `Visualizer(visible=False)`
- 16 ms 定时器 → `poll_events` + `update_renderer` + `capture_screen_float_buffer`
- numpy → QImage → QPixmap → `QLabel`

升级路径：后期切到 `QOpenGLFramebufferObject` 共享 GL 上下文，免 CPU 回读。`ViewerService` 是唯一对外接口，升级是局部的。

### 6.4 插件机制

每个插件是一个 Python 包：

```toml
# src/pccm/plugins/matlab/<name>/plugin.toml
[plugin]
name = "ground_filter_csf"
version = "0.1.0"
entry = "pccm.plugins.matlab.ground_filter_csf.algorithm"
author = ""
description = "Cloth Simulation Filter ported from MATLAB"
license = "GPL-3.0"
```

发现顺序（同名先到先得）：
1. `pccm.plugins.matlab.*`（内置）
2. `~/.config/pccm/plugins/`（用户级）
3. `./plugins/`（项目级）

`PluginManager.load_all()` 在主窗口显示前调用一次，失败插件只记录 `error`、UI 灰显，不影响主程序。

---

## 7. MATLAB → Python 迁移

每个 MATLAB 算法（参见 `src/pccm/plugins/matlab/README.md`）：

1. **解析**：`python tools/matlab_to_python/docstring_extractor.py func.m` → YAML
2. **脚手架**：`python tools/matlab_to_python/template_algorithm.py <name>` → 插件目录
3. **捕获参考**：MATLAB 跑一次，存 `output_expected.npy`
4. **移植**：MATLAB `Nx3 double` → `numpy.ndarray (N, 3) float64`；用 open3d / scipy 等价 API
5. **单测**：`np.testing.assert_allclose(rtol=1e-5, atol=1e-6)`
6. **集成测试**：pytest-qt 走菜单路径
7. **注册 & 文档**：插件 import 时自动注册

**已完成的移植**：`ground_filter_csf`（CSF 布料模拟地面滤波）。

---

## 8. 多人协同

- **分支模型**：GitHub Flow（`main` 受保护 + `feature/*` 短命 + `release/x.y.z`）
- **PR 审查**：`CODEOWNERS` 指定模块 owner + 至少 1 个其他工程师
- **DoD 检查清单**：`ruff` / `mypy` / `import-linter` / `pytest` 全绿；`CHANGELOG.md` 更新；新算法含参考对比测试
- **CI**：lint + 3 OS 测试矩阵 + GUI 测试

详见 `docs/architecture.md` § 8。

---

## 9. 当前状态 & 路线图

- ✅ **M0 骨架**（已完成）：仓库、`pyproject.toml`、pre-commit、CI 在空包上绿；core + algorithms + io + spatial + tools + utils + gui + plugins + tests 全套骨架；PyInstaller spec 可用
- 🚧 **M1 MVP**（4 周）：PLY/LAS 读写、offscreen 3D 视图、DB 树、属性面板、滤波（voxel/SOR/ROR）、矩形选择、删除、裁剪
- 📋 **M2 几何与配准**（4 周）：法向量/曲率/密度/RANSAC/DBSCAN、ICP、FPFH+RANSAC、C2C/C2M/M3C2、标量场
- 📋 **M3 网格/工具/插件**（4 周）：Poisson、剖面、量测、M3C2 自实现、插件管理器
- 📋 **M4 打磨与发布**（3 周）：E57 完整、Octree 可视化、3 OS 打包、签名、公证、用户文档

---

## 10. 贡献者

- PCCM Team
- 灵感来源：[CloudCompare](https://github.com/CloudCompare/CloudCompare)（GPL-3.0）
- 3D 引擎：[Open3D](https://github.com/isl-org/Open3D)
- GUI：[PySide6](https://doc.qt.io/qtforpython-6/)
- I/O：[laspy](https://pypi.org/project/laspy/) / [pye57](https://pypi.org/project/pye57/) / [plyfile](https://pypi.org/project/plyfile/)

## 11. 许可证

GPL-3.0-or-later — 见 [LICENSE](LICENSE)。

## 12. 详细文档

- [docs/architecture.md](docs/architecture.md) — 完整架构说明（12 节）
- [docs/plugin_author_guide.md](docs/plugin_author_guide.md) — 插件作者指南
- [src/pccm/plugins/matlab/README.md](src/pccm/plugins/matlab/README.md) — MATLAB 移植 7 步流程
- [CHANGELOG.md](CHANGELOG.md) — 变更日志
- [pyinstaller/pccm.spec](pyinstaller/pccm.spec) — 打包配置
