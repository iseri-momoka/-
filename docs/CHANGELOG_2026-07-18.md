# ccViewer Slim — 变更日志

> 日期: 2026-07-18
> 编译环境: Visual Studio 2026 + Qt 6.8.0 + MSVC 19.51

---

## 一、已完成的变更

### 1. 日志文件保存功能（新增）

**文件:** `ccViewer/ccviewerlog.h`、`ccViewer/main.cpp`、`ccViewer/ccviewer.cpp`

- 扩展 `ccViewerLog` 类，从仅错误弹窗改为完整的文件日志记录器
- 日志文件路径: `<exeDir>/logs/ccViewer_YYYYMMDD_HHMMSS.log`
- 格式: `[时间戳] [级别] 消息内容`，级别映射: V/S/I/W/E
- 构造时自动创建 logs 目录，析构时写入 footer 并关闭文件
- `main.cpp` 中启用 `ccLog::EnableMessageBackup(true)` 捕获启动阶段日志
- `dispToConsole()` 同时写入日志文件，覆盖所有插件/API 消息

### 2. 处理功能修复 — P0（4/4）

#### 2a. `doActionComputeNormals()` — 法线计算
**文件:** `ccViewer/ccviewer.cpp`

- 支持两种计算模式:
  - **Grid 模式**: `cloud->computeNormalsWithGrids(minGridAngle, progressDlg, preferredOrientation)`
  - **Octree 模式**: `cloud->computeNormalsWithOctree(localModel, preferredOrientation, radius, progressDlg)`
- 支持 MST 法线方向调整: `cloud->orientNormalsWithMST(neighborCount, progressDlg)`
- 新增 `#include <ccProgressDialog.h>` 提供进度条

#### 2b. `doActionSubsample()` — 降采样
**文件:** `ccViewer/ccviewer.cpp`（已有实现，无需修改）

#### 2c. `doActionFilterByValue()` — 按值过滤
**文件:** `ccViewer/ccviewer.cpp`

- 改用 `sf->getValue(i)` 正确读取标量值（原 `cloud->getScalarValue()` 不存在）
- **SPLIT 模式**: 分离为 inside/outside 两个点云
- **EXPORT 模式**: 仅保留范围内点云
- 使用 `ReferenceCloud` + `partialClone()` 创建新点云
- 新增 `#include <ScalarField.h>`

#### 2d. `doActionSORFilter()` — 统计离群点去除（新实现）
**文件:** `ccViewer/ccviewer.cpp`

- 使用 `CCCoreLib::CloudSamplingTools::sorFilter(cloud, knn, nSigma)` 执行 SOR
- 返回 `ReferenceCloud*`，通过 `partialClone()` 创建过滤后的新云
- 原始云隐藏，新云添加到数据库
- 新增 `#include <CloudSamplingTools.h>`

### 3. P2 — 代码质量修复（5 项）

| # | 修改 | 文件 |
|---|------|------|
| 1 | 删除废弃 `Qt::AA_EnableHighDpiScaling`（Qt6 默认启用） | `main.cpp:49-52` |
| 2 | 删除冗余 `setStyleSheet(QString())` | `ccviewer.cpp:102` |
| 3 | `cmake_minimum_required` 3.10 → 3.16（Qt6 最低要求） | `CMakeLists.txt:1` |
| 4 | LTO 配置改用 `check_ipo_supported()` + generator expression（支持 VS 多配置生成器） | `CMakeSetCompilerOptions.cmake:17-23` |
| 5 | 移除 `_SECURE_SCL=0`（禁用检查迭代器，掩盖潜在 bug） | `CMakeSetCompilerOptions.cmake:38` |

### 4. 构建系统修复

| 修改 | 文件 |
|------|------|
| CMakePresets.json: generator 改为 `Visual Studio 18 2026`，添加 `architecture` | `CMakePresets.json` |
| in-source build 检测: 改为 `string(TOLOWER)` 比较（修复路径大小写/格式问题） | `CMakeLists.txt:5-9` |

---

## 二、编译错误修复

首次编译发现并修复了以下问题:

| 错误 | 原因 | 修复 |
|------|------|------|
| `C2027: 使用了未定义类型"QCoreApplication"` | `ccviewerlog.h` 缺少 `#include <QCoreApplication>` | 添加 include |
| `C2039: "setCodec" 不是 "QTextStream" 的成员` | Qt6 移除了 `QTextStream::setCodec()`（默认 UTF-8） | 删除 `setCodec` 调用 |
| `C2079: "progressDlg" 使用未定义的 class "ccProgressDialog"` | `ccviewer.cpp` 缺少 include | 添加 `#include <ccProgressDialog.h>` |
| `C2039: "getScalarValue" 不是 "ccPointCloud" 的成员` | API 不存在于本代码库 | 改为 `sf->getValue(i)`（ScalarField 成员函数） |
| `LNK2001: 无法解析的外部符号 "s_instance"` | header-only 类中 `static` 成员需 out-of-class 定义 | 改为 `inline static`（C++17） |

---

## 三、构建验证

```
cmake .. -G "Visual Studio 18 2026" -A x64 -DCMAKE_PREFIX_PATH="C:/Qt/6.8.0/msvc2022_64"
cmake --build . --config Release --parallel
```

✅ 构建成功，输出: `build2/ccViewer/Release/ccViewer.exe` (332KB)

---

## 四、尚未完成的优化项

### P1 — 高优先级（性能）
- [ ] Python 工具改为异步 QProcess（消除 UI 冻结）
- [ ] CSV 导出批量写入优化
- [ ] 场景增量加载（消除多文件拖放时的 UI 冻结）
- [ ] 关键裸指针改为 `std::unique_ptr`

### P2 — 中优先级（代码质量）
- [ ] 提取重复的对话框构建代码为工具函数
- [ ] `ccApplicationBase.cpp:88` 废弃的 `Qt::AA_ShareOpenGLContexts`（需同步改上游代码）

### P3 — 低优先级（清理）
- [ ] 清理空方法体（`on3DMouseKeyUp`、`freezeUI`）
- [ ] `FileIOFilter.cpp` 拼写错误修正 "Sesion" → "Session"
- [ ] 删除重复的 `CCCoreLib-master/` 目录
