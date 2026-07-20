# ccViewer SLIM (MSVC)

基于 CloudCompare 的轻量级点云查看器，使用 MSVC 编译。

## 功能特性

- **文件操作**：打开/保存多种点云格式（LAS、LAZ、TXT、XYZ、PLY、OBJ、STL 等）
- **点云处理**：
  - 法线计算
  - 子采样
  - 按标量值过滤
  - SOR 异常值过滤
- **工具菜单**：
  - 裁剪框（Clip by Box）
  - TLS 平面拟合（Python 脚本）
  - 点到平面投影（Python 脚本）
  - KNN 最近邻搜索（Python 脚本）
  - 旋转矩阵计算（Python 脚本）

## 依赖

- **Windows 10/11** (MSVC 编译器)
- **Qt 6.x** (推荐 Qt 6.5+)
- **CMake 3.10+**
- **Python 3.x** (用于 Python 脚本功能)
- **CCCoreLib** (外部依赖库)

## 构建步骤

### 1. 克隆仓库

```bash
git clone --recursive https://github.com/iseri-momoka/-.git
cd ccViewer-slim-msvc
```

### 2. 安装外部依赖

```bash
# 安装 CCCoreLib
cd libs/qCC_db/extern
git clone --depth 1 https://github.com/CloudCompare/CCCoreLib.git
cd ../../..
```

### 3. 配置和构建

```bash
# 使用 CMake 预设（推荐）
cmake --preset slim

# 或手动配置
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DPLUGIN_IO_QCORE=ON -DPLUGIN_IO_QLAS=ON

# 构建
cmake --build build --config Release --parallel
```

### 4. 运行

构建完成后，可执行文件位于 `build/ccViewer/` 目录。

## 目录结构

```
.
├── ccViewer/           # 主应用程序源码
│   ├── ccviewer.h/cpp  # 主窗口实现
│   ├── main.cpp        # 程序入口
│   └── ui_templates/   # Qt UI 文件
├── libs/               # 内部库
│   ├── CCFbo/
│   ├── qCC_db/         # 核心数据模型
│   ├── qCC_io/         # 文件I/O
│   └── CCAppCommon/    # 通用应用组件
├── plugins/            # 插件
│   ├── core/
│   │   ├── qCoreIO/    # 核心格式 (OBJ/STL/VTK/OFF/PTX)
│   │   └── qLASIO/     # LAS/LAZ/COPC 格式
│   └── cmake/          # 插件构建工具
├── qCC_selected/       # 从 qCC 提取的代码
│   ├── dialogs/        # 处理对话框
│   ├── support/        # 工具类
│   └── ui_templates/   # UI 文件
├── python/             # Python 计算脚本
│   ├── tls_plane.py    # TLS 平面拟合
│   ├── point_projection.py  # 点到平面投影
│   ├── knn_search.py   # KNN 搜索
│   └── rotation_matrix.py  # 旋转矩阵计算
└── cmake/              # CMake 模块
```

## Python 脚本使用

### TLS 平面拟合

```bash
python python/tls_plane.py input.csv output.json
```

输入：CSV 格式的点云 (x,y,z)
输出：JSON 格式的平面参数 (a,b,c,d)

### 点到平面投影

```bash
python python/point_projection.py points.csv plane.json projected.csv
```

### KNN 搜索

```bash
python python/knn_search.py query.csv points.csv k results.json
```

### 旋转矩阵计算

```bash
python python/rotation_matrix.py normal1.json normal2.json rotation.json
```

## 开发说明

### 构建选项

- `OPTION_MP_BUILD`: 多线程编译（默认 ON）
- `OPTION_BUILD_CCVIEWER`: 构建 ccViewer（默认 ON）
- `PLUGIN_IO_QCORE`: 核心 I/O 插件（默认 ON）
- `PLUGIN_IO_QLAS`: LAS 格式插件（默认 ON）

### 代码规范

- 使用 C++17 标准
- 遵循 Qt 编码风格
- 使用 clang-format 格式化代码（配置文件已提供）

## 许可证

GNU General Public License v2 或更高版本
