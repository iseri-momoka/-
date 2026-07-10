# PCCM — Point Cloud Compare & Manage

> C++ 编译前端（CloudCompare）+ Python 算法后端（MATLAB→Python 移植）的 3D 点云处理桌面软件。

![status](https://img.shields.io/badge/status-M1%20frontend%20built-brightgreen)
![cpp](https://img.shields.io/badge/cpp-CloudCompare-blue)
![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![license](https://img.shields.io/badge/license-GPL--3.0-green)
![gui](https://img.shields.io/badge/gui-Qt%206.8-purple)
![engine](https://img.shields.io/badge/engine-open3d-orange)

---

## 1. 项目是什么

PCCM（Point Cloud Compare & Manage）是一个**点云处理桌面软件**，采用**方案A 架构**：

- **前端**：编译 CloudCompare C++ 源码为独立可执行文件，保留核心功能（I/O、可视化、编辑、滤波）
- **后端**：Python CLI 算法库，由 MATLAB 代码渐进式移植而来，通过命令行/管道与前端通信
- **算法层**：open3d + scipy + numpy + scikit-learn

设计目标：

- **编译级性能**：前端用 C++/Qt 原生速度处理大点云交互
- **算法灵活性**：Python 后端可独立迭代，支持 MATLAB→Python 7 步迁移流程
- **插件机制**：Python 算法以插件形式注册，通过 CLI 接口被前端调度
- **多人协同**：C++ 前端 + Python 后端分层开发，互不阻塞

---

## 2. 已经完成的工作

> 截止 2026-07-11，前端编译完成，Python 后端骨架完成。

### ✅ 前端编译（C++ / Qt）

| 组件 | 状态 | 说明 |
|---|---|---|
| CloudCompare 前端 | ✅ 已编译 | `build/qCC/Release/CloudCompare.exe`（Release x64） |
| CCViewer 轻量查看器 | ✅ 已编译 | `build/ccViewer/Release/ccViewer.exe` |
| CCCoreLib 核心库 | ✅ 已编译 | `build/libs/qCC_db/extern/CCCoreLib/Release/CCCoreLib.dll` |
| QCC_DB_LIB 数据层 | ✅ 已编译 | `build/libs/qCC_db/Release/QCC_DB_LIB.dll` |
| QCC_GL_LIB 渲染层 | ✅ 已编译 | `build/libs/qCC_glWindow/Release/QCC_GL_LIB.dll` |
| QCC_IO_LIB I/O层 | ✅ 已编译 | `build/libs/qCC_io/Release/QCC_IO_LIB.dll` |
| CCAppCommon 公共层 | ✅ 已编译 | `build/libs/CCAppCommon/Release/CCAppCommon.dll` |
| QCORE_IO_PLUGIN | ✅ 已编译 | `build/plugins/core/IO/qCoreIO/Release/QCORE_IO_PLUGIN.dll` |
| Qt 6.8.0 环境 | ✅ 已配置 | `C:\Qt\6.8.0\msvc2022_64\` |
| MSVC 2022 (v19.51) | ✅ 已配置 | `D:\vs2026\` |
| CMake 4.4.0 | ✅ 已配置 | `C:\Program Files\CMake\bin\cmake.exe` |

**功能保留（裁剪后）**：文件 I/O（PLY/LAS/PCD/ASC/DXF/SHP/STL/OBJ/PLY）、3D 可视化、编辑（克隆/合并/变换）、基础滤波（体素/SOR/噪声/统计检验）、几何（法向量/曲率/RANSAC/DBSCAN）、配准（ICP/4PCS）、距离（C2C/C2M）、网格操作、传感器投影、剖面提取。

**已裁剪**：M3C2 插件（后端自实现）、栅格化、Qhull（不常用插件依赖）。

### ✅ Python 后端骨架（M0）

| 子系统 | 文件数 | 内容 |
|---|---:|---|
| 项目根配置 | 11 | `pyproject.toml`、CI、pre-commit、ruff、mypy、import-linter |
| `core/` | 6 | Document、History、Signals、Types、Errors |
| `algorithms/` | 23 | base + registry + 7 个子包 |
| `io/` | 7 | LAS/PLY/PCD/OBJ/E57 读写 |
| `spatial/` | 2 | KDTree、Octree |
| `tools/` | 5 | 选择/分割/裁剪/剖面/量测 |
| `gui/` | 16 | MainWindow + Viewer + Panel |
| `plugins/` | 7 | api + CSF 移植 |
| `tests/` | 9 | conftest + 8 个测试文件 |
| **合计** | **~106** | + 配置 / CI / 文档 |

---

## 3. 仓库结构

```
点云软件开发/
├── README.md                   # ← 本文件
├── CLAUDE.md                   # Claude Code 协作指南
├── pyproject.toml              # Python 后端配置、依赖锁、工具配置
├── .gitignore
├── .pre-commit-config.yaml     # pre-commit 钩子（ruff + mypy + import-linter）
├── .ruff.toml / mypy.ini       # lint & 类型配置
├── importlinter.ini            # 分层契约
├── pytest.ini
├── LICENSE                     # GPL-3.0-or-later
├── CHANGELOG.md                # 变更日志
├── CODEOWNERS                  # 模块所有权
│
├── 原软件代码/                  # ★ CloudCompare C++ 前端源码
│   ├── CloudCompare-master/    # CloudCompare 源码（含 .gitmodules）
│   │   ├── qCC/               # 前端主程序（mainwindow.cc*.h/.cpp，80+ 文件）
│   │   ├── ccViewer/          # 轻量查看器
│   │   ├── libs/              # 核心库
│   │   │   ├── CCCoreLib      # 数学/几何/配准核心
│   │   │   ├── qCC_db         # 数据模型层（ccPointCloud/ccMesh）
│   │   │   ├── qCC_glWindow   # OpenGL 渲染
│   │   │   ├── qCC_io         # 文件 I/O 过滤器
│   │   │   ├── CCAppCommon    # 公共 UI 组件
│   │   │   └── CCPluginAPI    # 插件接口
│   │   ├── plugins/           # 标准插件（qCoreIO、qPoissonRecon 等）
│   │   └── build/             # ★ 编译输出（Release x64）
│   │       ├── qCC/Release/CloudCompare.exe
│   │       └── ccViewer/Release/ccViewer.exe
│   └── qCC文件说明.txt          # 功能→代码映射速查
│
├── docs/                       # 文档
│   ├── architecture.md         # 完整架构说明（12 节）
│   ├── cloudcompare_frontend_analysis.md  # CloudCompare 源码分析
│   ├── plugin_author_guide.md  # 插件作者指南
│   └── matlab_port_workflow.md # MATLAB→Python 迁移流程
│
├── src/pccm/                   # Python 后端源码（src 布局）
│   ├── core/                   # ★ 禁止 import PySide6
│   │   ├── document.py         # Document / Entity
│   │   ├── history.py          # 命令模式 undo/redo
│   │   ├── signals.py          # blinker 事件总线
│   │   ├── types.py
│   │   └── errors.py
│   ├── algorithms/             # ★ 禁止 import PySide6
│   │   ├── base.py             # Algorithm / ParamSpec / Result 协议
│   │   ├── registry.py         # AlgorithmRegistry 中央调度
│   │   ├── filter/ geometry/ registration/ distance/ scalar_field/ mesh/
│   │   └── ...
│   ├── io/                     # LAS/PLY/PCD/OBJ/E57 读写
│   ├── spatial/                # KDTree / Octree 封装
│   ├── tools/                  # 选择 / 裁剪 / 剖面 / 量测
│   ├── gui/                    # ★ PySide6 唯一入口
│   ├── plugins/                # 插件（Qt-free）
│   └── utils/                  # 日志 / 进度 / colormap / 单位
│
├── tests/                      # 测试（unit / integration / gui）
├── tools/matlab_to_python/     # MATLAB→Python 迁移工具
├── scripts/                    # 一次性脚本
├── pyinstaller/                # 打包配置
└── .github/workflows/ci.yml    # CI：lint + 三系统测试
```

---

## 4. 技术栈与版本要求

### 4.1 C++ 前端（CloudCompare）

| 组件 | 版本 | 路径/说明 |
|---|---|---|
| CloudCompare 源码 | `master`（2026-07） | `原软件代码/CloudCompare-master/` |
| CMake | `4.4.0` | `C:\Program Files\CMake\bin\cmake.exe` |
| MSVC (Visual Studio) | `v19.51`（VS 2022） | `D:\vs2026\`（检测为 Visual Studio 18 2026） |
| Qt | `6.8.0` MSVC 2022 64-bit | `C:\Qt\6.8.0\msvc2022_64\`（via aqtinstall） |
| Windows SDK | `10.0.26100.0` | 自动检测 |
| OpenMP | 已启用 | CMake 自动发现 |
| 编译配置 | `Release x64` | `build/qCC/Release/CloudCompare.exe` |

**子模块（15 个，全部已 clone）**：

| 子模块 | 用途 |
|---|---|
| CCCoreLib | 核心数学/几何/配准 |
| MeshIO | 网格 I/O 插件 |
| libE57Format | E57 格式支持 |
| PoissonRecon | Poisson 重建 |
| QDarkStyleSheet | 暗色主题 |
| quazip | ZIP 支持 |
| dlib | 机器学习库 |
| q3DMASC / qTreeIso / qVoxFall / qG3Point / qMPlane / qColorimetricSegmenter / qMasonry / qJSonRPCPlugin | 各标准插件 |

### 4.2 Python 后端（运行时）

| 包 | 版本 | 用途 |
|---|---|---|
| Python | `>=3.11,<3.13` | 3.13 wheel 滞后 |
| numpy | `>=2.0,<3` | 算法基础 |
| scipy | `>=1.13,<2` | cKDTree、griddata |
| scikit-learn | `>=1.5,<2` | DBSCAN 兜底 |
| **open3d** | `>=0.19,<0.20` | **3D 引擎（核心）** |
| **PySide6** | `>=6.7,<6.9` | **GUI（LGPL）** |
| matplotlib | `>=3.9,<4` | 直方图面板 |
| laspy | `>=2.5,<3` | LAS / LAZ |
| pye57 | `>=0.4` | E57 |
| plyfile | `>=1.1` | PLY 兜底 |
| shapely | `>=2.0` | 多边形选择 |
| qtconsole | `>=5.5` | Python 控制台 |
| blinker | `>=1.7` | core 事件总线 |

### 4.3 开发与测试

| 包 | 版本 | 用途 |
|---|---|---|
| pytest | `>=8` | 单元/集成测试 |
| pytest-qt | `>=4.4` | GUI 测试 |
| pytest-cov | `>=5` | 覆盖率 |
| ruff | `>=0.6` | lint + format |
| mypy | `>=1.11` | 类型检查 |
| import-linter | `>=2` | 分层契约 |
| pre-commit | `>=4` | 钩子运行器 |
| pyinstaller | `>=6.10` | 打包 .exe |

### 4.4 系统要求

- **Windows 10/11**（当前开发平台）/ **macOS 12+** / **Ubuntu 22.04+**
- 8 GB RAM 起步，处理 50M+ 点云建议 16 GB+
- 支持 OpenGL 3.3+ 的显卡（CloudCompare / open3d 可视化）
- 磁盘：CloudCompare 编译输出约 200 MB；Python 后端 + open3d wheel 约 1.5 GB

---

## 5. 快速开始

### 5.1 编译 CloudCompare 前端

**前置条件**：CMake 4.4.0 + MSVC 2022 + Qt 6.8.0（已装好可跳过）

```bash
# 1. 安装 Qt 6.8.0（如果没有）
pip install aqtinstall
aqt install-qt windows desktop 6.8.0 win64_msvc2022_64 -O C:\Qt

# 2. 初始化子模块
cd 原软件代码/CloudCompare-master
git submodule update --init --recursive
# 如果子模块为空（源码被整体复制），手动 clone：
git clone --depth 1 https://github.com/CloudCompare/CCCoreLib libs/qCC_db/extern/CCCoreLib
cd libs/qCC_db/extern/CCCoreLib && git submodule update --init --depth 1
cd ../../../..
git clone --depth 1 https://github.com/CloudCompare/MeshIO.git plugins/core/IO/MeshIO

# 3. CMake 配置
cmake -S . -B build -DCMAKE_PREFIX_PATH='C:\Qt\6.8.0\msvc2022_64' -G 'Visual Studio 18 2026' -A x64

# 4. 编译
cmake --build build --config Release -- /m

# 5. 运行
build/qCC/Release/CloudCompare.exe
```

编译输出位于 `build/` 目录。

### 5.2 Python 后端开发

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

### 5.3 验证安装

```bash
# lint
ruff check src tests
mypy src/pccm
lint-imports                     # import-linter 契约

# 测试（无 GUI）
pytest -m "not gui" -v

# GUI 测试（Linux 需要 xvfb）
xvfb-run pytest -m gui -v
```

### 5.4 打包

```bash
# 生成 standalone
pyinstaller pyinstaller/pccm.spec
# 产物在 dist/pccm/
```

---

## 6. 架构核心

### 6.1 方案A 架构：C++ 前端 + Python 后端

```
┌───────────────────────────────────────────────┐
│         CloudCompare C++ (Qt 6.8)             │
│  ┌──────┐ ┌──────────┐ ┌──────────┐           │
│  │DB 树 │ │3D 视口    │ │属性面板  │           │
│  └──┬───┘ └────┬─────┘ └──────────┘           │
│     │          │                               │
│  ┌──▼──────────▼──────────────────────────┐   │
│  │  qCC 前端 (main.cpp)                   │   │
│  │  - 文件 I/O (PLY/LAS/PCD/ASC/DXF...)  │   │
│  │  - 3D 可视化 (OpenGL)                  │   │
│  │  - 编辑/滤波/配准/距离/网格            │   │
│  │  - CLI 接口 (ccCommandLineInterface)   │   │
│  └──────────────┬────────────────────────┘   │
│                 │ 命令行/管道                  │
└─────────────────┼─────────────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────────────┐
│         Python CLI 算法后端                    │
│  ┌───────────────────────────────────────┐   │
│  │  pccm.algorithms                      │   │
│  │  - filter/  (voxel/SOR/ROR)          │   │
│  │  - geometry/ (normals/curvature/RANSAC)│  │
│  │  - registration/ (ICP/FPFH)          │   │
│  │  - distance/ (C2C/C2M/M3C2)          │   │
│  │  - mesh/ (Poisson/decimate)          │   │
│  └───────────────────────────────────────┘   │
│  ┌───────────────────────────────────────┐   │
│  │  plugins/                              │   │
│  │  - matlab/ground_filter_csf (CSF)     │   │
│  │  - matlab/* (更多 MATLAB 移植)        │   │
│  └───────────────────────────────────────┘   │
│  依赖：open3d + scipy + numpy + scikit-learn │
└───────────────────────────────────────────────┘
```

### 6.3 CloudCompare C++ 前端

- 源码位于 `原软件代码/CloudCompare-master/`
- 核心入口：`qCC/main.cpp` → `MainWindow`（2700+ 行）
- 数据模型：`ccPointCloud`、`ccMesh`、`ccHObject`（`libs/qCC_db/`）
- 渲染：OpenGL + FBO（`libs/qCC_glWindow/`、`libs/CCFbo/`）
- I/O：文件过滤器插件体系（`libs/qCC_io/` + `plugins/core/IO/`）
- CLI：`ccCommandLineInterface` 支持无 GUI 批处理
- 详细分析：[docs/cloudcompare_frontend_analysis.md](docs/cloudcompare_frontend_analysis.md)

### 6.4 Python 后端

- 核心数据流：

```
用户操作 → QAction → QDialog（由 ParamSpec 自动生成）
       → Algorithm.run(ctx, **values)
       → open3d PointCloud / Mesh
       → Document.add_*  / replace
       → blinker signals
       → ViewerService / DBTreePanel / PropertiesPanel
       → Open3DWidget（offscreen blit 至 QLabel）
```

- `pccm.core / algorithms / io / spatial / tools / plugins` **禁止** import `pccm.gui` 或 `PySide6`
- `pccm.algorithms / plugins` **禁止** import `open3d.visualization`（用 headless API）
- plugins.matlab 只能 import `pccm.plugins.api` 受控表面

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

- ✅ **M0 骨架**（已完成）：仓库配置 + Python 后端 124 文件骨架 + CI/CD
- ✅ **M1 前端编译**（已完成）：CloudCompare C++ 编译成功，Release x64，核心功能保留
- 🚧 **M1 后端 MVP**（4 周）：PLY/LAS 读写、offscreen 3D 视图、DB 树、滤波（voxel/SOR/ROR）
- 📋 **M2 几何与配准**（4 周）：法向量/曲率/RANSAC/DBSCAN、ICP、C2C/C2M/M3C2
- 📋 **M3 网格/工具/插件**（4 周）：Poisson、剖面、量测、更多 MATLAB 移植
- 📋 **M4 打磨与发布**（3 周）：E57 完整、3 OS 打包、签名、用户文档

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
