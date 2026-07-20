---
name: cc-slim-project
description: CloudCompare 精简版项目概况，位于 cc次开发/二次开发代码/
metadata: 
  node_type: memory
  type: project
  originSessionId: 65d660c8-9716-4f3f-b36b-ef5069f17cc8
---

## 项目概况

在 `c:\Users\xklin\Desktop\cc二次开发\二次开发代码\` 搭建了 CloudCompare 精简版。

### 架构
- 基于 **ccViewer**（轻量 3D 查看器）扩充
- 从 qCC 精选了 8 个核心点云处理对话框加入
- 不编译 qCC 主程序，不编译 33 个插件中的 32 个

### 已包含的库（原样，未改动）
- libs/ 全部 7 个：CCFbo, qCC_db, qCC_io, qCC_glWindow, CCPluginStub, CCPluginAPI, CCAppCommon
- 仅插件 qCoreIO（OBJ/STL/VTK/OFF/PTX）+ cmake/Plugins.cmake

### 已加入的处理对话框（从 qCC 复制）
- ccNormalComputationDlg（法线计算）
- ccSubsamplingDlg（点云采样）
- ccFilterByValueDlg（按 SF 值过滤）
- ccSORFilterDlg（SOR 离群点去除）
- ccComparisonDlg（云间/云网距离）
- ccRegistrationDlg（ICP 配准）
- ccAlignDlg（4PCS 对齐）
- ccGraphicalSegmentationTool（交互式分割）

### 需手动获取的依赖
- **CCCoreLib**：git clone 到 libs/qCC_db/extern/CCCoreLib/（GitHub 不可访问时另寻途径）
- **LASzip**：如需 LAS 格式支持，可选安装

### 构建命令
```bash
cd "二次开发代码"
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DPLUGIN_IO_QCORE=ON -DOPTION_USE_DXF_LIB=OFF -DOPTION_USE_SHAPE_LIB=OFF
cmake --build . --config Release --parallel
```

### 原代码位置
`c:\Users\xklin\Desktop\cc二次开发\原软件代码\CloudCompare-master\`

### 说明表文件
- CloudCompare-libs-说明表.txt（libs/ 下 7 个库说明）
- CloudCompare-plugins-说明表.txt（plugins/ 下 34 个插件说明）
- CloudCompare-ccViewer-说明表.txt（ccViewer 文件说明）
