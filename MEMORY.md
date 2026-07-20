# CloudCompare 精简版项目

## 位置
`c:\Users\xklin\Desktop\cc二次开发\二次开发代码\`

## 架构
基于 **ccViewer**（轻量 3D 查看器）扩充，从 qCC 精选了 8 个核心点云处理对话框加入。
不编译 qCC 主程序，不编译 33 个插件中的 32 个。

## 已包含的库（原样，未改动）
- libs/ 全部 7 个：CCFbo, qCC_db, qCC_io, qCC_glWindow, CCPluginStub, CCPluginAPI, CCAppCommon
- 仅插件 qCoreIO（OBJ/STL/VTK/OFF/PTX）+ cmake/Plugins.cmake

## 已加入的处理对话框（从 qCC 复制）
| 对话框 | 功能 |
|--------|------|
| ccNormalComputationDlg | 法线计算 |
| ccSubsamplingDlg | 点云采样 |
| ccFilterByValueDlg | 按标量场值过滤 |
| ccSORFilterDlg | SOR 离群点去除 |
| ccComparisonDlg | 云间/云网距离计算 |
| ccRegistrationDlg | ICP 配准 |
| ccAlignDlg | 4PCS 对齐 |
| ccGraphicalSegmentationTool | 交互式图形分割 |

## Python/MATLAB 插件预留
- ccViewer 已添加 `loadStandardPlugins()` 方法和 `menuPlugins` 菜单
- Standard 类型的插件 DLL 放入 plugins/ 目录即可被自动加载
- Python 插件实现路径：编写嵌入 CPython 的 Standard 插件 DLL

## 需手动获取的依赖
- **CCCoreLib**：git clone 到 `libs/qCC_db/extern/CCCoreLib/`
  ```bash
  cd "二次开发代码/libs/qCC_db/extern"
  git clone --depth 1 https://github.com/CloudCompare/CCCoreLib.git
  ```
- **LASzip**：如需 LAS 格式支持，可选安装

## 构建命令
```bash
cd "c:\Users\xklin\Desktop\cc二次开发\二次开发代码"
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DPLUGIN_IO_QCORE=ON -DOPTION_USE_DXF_LIB=OFF -DOPTION_USE_SHAPE_LIB=OFF -DOPTION_USE_GDAL=OFF
cmake --build . --config Release --parallel
```

## 前端要求
- CMake 3.10+
- Qt 6.4+
- C++17 编译器（MSVC 2019+ 或 MinGW）

## 原代码位置
`c:\Users\xklin\Desktop\cc二次开发\原软件代码\CloudCompare-master\`

## 说明表文件
- CloudCompare-libs-说明表.txt
- CloudCompare-plugins-说明表.txt
- CloudCompare-ccViewer-说明表.txt
