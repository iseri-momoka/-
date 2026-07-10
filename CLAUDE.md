# CLAUDE.md — PCCM 项目协作指南

> 本文件为 Claude Code 和团队成员提供项目上下文，确保每次会话都能快速理解项目结构和约束。

## 项目概述

PCCM（Point Cloud Compare & Manage）是一个 3D 点云处理桌面软件，采用 **方案A 架构**：

- **前端**：CloudCompare C++ 源码编译（Qt 6.8 + MSVC 2022）
- **后端**：Python CLI 算法库（open3d + scipy + numpy），支持 MATLAB→Python 移植
- **通信**：命令行/管道（CloudCompare CLI → Python 脚本）

## 构建环境

| 工具 | 版本 | 路径 |
|---|---|---|
| CMake | 4.4.0 | `C:\Program Files\CMake\bin\cmake.exe` |
| MSVC | v19.51 (VS 2022) | `D:\vs2026\` |
| Qt | 6.8.0 msvc2022_64 | `C:\Qt\6.8.0\msvc2022_64\` |
| Python | 3.11 / 3.12 | `.venv\` |

### 编译 CloudCompare 前端

```bash
cd 原软件代码/CloudCompare-master
# 如果子模块为空，先 clone：
git clone --depth 1 https://github.com/CloudCompare/CCCoreLib libs/qCC_db/extern/CCCoreLib
cd libs/qCC_db/extern/CCCoreLib && git submodule update --init --depth 1 && cd ../../../..
git clone --depth 1 https://github.com/CloudCompare/MeshIO.git plugins/core/IO/MeshIO

# 配置 + 编译
cmake -S . -B build -DCMAKE_PREFIX_PATH='C:\Qt\6.8.0\msvc2022_64' -G 'Visual Studio 18 2026' -A x64
cmake --build build --config Release -- /m

# 输出
# build/qCC/Release/CloudCompare.exe
# build/ccViewer/Release/ccViewer.exe
```

## 关键约束（必须遵守）

### 分层规则（import-linter 强制）

1. `pccm.core / algorithms / io / spatial / tools / plugins` **禁止** import `pccm.gui` 或 `PySide6`
2. `pccm.algorithms / plugins` **禁止** import `open3d.visualization`
3. `pccm.plugins.matlab` 只能 import `pccm.plugins.api`，**禁止** `pccm.gui` / `pccm.core.document` / `pccm.core.history`

### 代码规范

- **Python**：ruff（line-length=100）、mypy（core/algorithms 用 strict）、import-linter
- **C++**：CloudCompare 自带 `.clang-format`
- **提交**：pre-commit 钩子自动运行 ruff + mypy + import-linter + yaml/toml 检查
- **PR**：需要 1 个 approve + CI 绿 + `CHANGELOG.md` 更新

### 分支模型

- `main`（受保护，禁直推）
- `feature/<topic>`（短命，PR 合并后删）
- `release/<version>`（从 main 切出，只接受 bugfix）

## 目录结构速查

```
点云软件开发/
├── 原软件代码/CloudCompare-master/  # C++ 前端源码
│   ├── qCC/                       # 主程序（mainwindow.cpp 2700+ 行）
│   ├── libs/                      # 核心库（CCCoreLib、qCC_db、qCC_glWindow、qCC_io）
│   ├── plugins/                   # 标准插件
│   └── build/                     # 编译输出
├── src/pccm/                      # Python 后端源码
│   ├── core/                      # Document/History/Signals（无 Qt）
│   ├── algorithms/                # 算法（filter/geometry/registration/distance/mesh）
│   ├── io/                        # 文件读写（LAS/PLY/PCD/OBJ/E57）
│   ├── spatial/                   # KDTree/Octree
│   ├── tools/                     # 选择/裁剪/剖面/量测
│   ├── gui/                       # PySide6 GUI（唯一允许 Qt 的层）
│   └── plugins/                   # 插件（matlab/ 下有 CSF 移植）
├── tests/                         # 测试
├── docs/                          # 文档
│   ├── cloudcompare_frontend_analysis.md  # CC 源码分析
│   └── architecture.md            # 完整架构说明
├── tools/matlab_to_python/        # MATLAB→Python 迁移工具
├── pyproject.toml                 # Python 配置
├── CLAUDE.md                      # ← 本文件
└── CODEOWNERS                     # 模块所有权
```

## 核心文件

| 文件 | 作用 |
|---|---|
| `src/pccm/core/document.py` | Document / Entity 数据模型 |
| `src/pccm/algorithms/base.py` | Algorithm / ParamSpec / Result 协议 |
| `src/pccm/algorithms/registry.py` | AlgorithmRegistry 中央调度 |
| `src/pccm/gui/viewer/o3d_widget.py` | open3d → Qt 桥（offscreen blit） |
| `src/pccm/plugins/api.py` | 插件公共 API（受控 re-export） |
| `原软件代码/.../qCC/mainwindow.cpp` | CloudCompare 主窗口（2700+ 行） |
| `原软件代码/.../libs/qCC_db/ccPointCloud.cpp` | 点云数据模型核心 |

## MATLAB→Python 迁移流程

7 步流程，详见 `docs/matlab_port_workflow.md`：
1. 解析 MATLAB 头注释 → YAML
2. 生成插件脚手架
3. 捕获 MATLAB 参考输出
4. 移植到 Python（numpy/open3d/scipy 等价 API）
5. 单测（`assert_allclose` 对比参考输出）
6. 集成测试（pytest-qt 走菜单路径）
7. 注册 & 文档

## 常见操作

```bash
# Python 后端 lint
ruff check src tests
ruff format src tests

# 类型检查
mypy src/pccm/core src/pccm/algorithms

# 分层契约检查
python -m importlinter

# 测试
pytest -m "not gui" -v
xvfb-run pytest -m gui -v  # Linux

# 重新编译 CloudCompare（修改 C++ 后）
cmake --build 原软件代码/CloudCompare-master/build --config Release -- /m
```
