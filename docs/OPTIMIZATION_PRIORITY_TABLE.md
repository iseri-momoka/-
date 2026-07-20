# ccViewer Slim — 优化优先级表

> 生成日期: 2026-07-18  
> 范围: `ccViewer-slim-full/ccViewer-slim-full/` 全代码库

---

## 一、优化总览

| 优先级 | 类别 | 数量 | 预估工作量 |
|--------|------|------|------------|
| **P0 — 必须** | 功能缺陷/数据安全 | 3 | 2-3天 |
| **P1 — 高** | 性能瓶颈 | 6 | 1-2周 |
| **P2 — 中** | 代码质量/构建优化 | 8 | 1-2周 |
| **P3 — 低** | 技术债务/清理 | 5 | 1-3天 |

---

## 二、P0 — 必须修复（功能缺陷/数据安全）

| # | 类别 | 文件:行 | 问题描述 | 影响 | 状态 |
|---|------|---------|----------|------|------|
| 1 | **功能缺陷** | `ccviewer.cpp:979-1048` | `doActionComputeNormals()` / `doActionSORFilter()` / `doActionFilterByValue()` 仅弹出对话框但不执行实际计算 | 4个处理功能完全不可用 | ✅ 已修复 |
| 2 | **功能缺陷** | `ccviewer.cpp:1018-1033` | `doActionFilterByValue()` 读取参数后无任何过滤操作 | 按值过滤功能为空壳 | ✅ 已修复 |
| 3 | **数据安全** | `ccviewer.cpp:1344-1368` | `runPythonScript()` 将用户文件路径直接传入 QProcess，无参数转义 | 桌面端路径注入风险 | ⏭ 无需修复（QProcess::start(QString, QStringList)不经shell，无注入风险）|

---

## 三、P1 — 高优先级（性能瓶颈）

| # | 类别 | 文件:行 | 问题描述 | 影响 | 建议方案 |
|---|------|---------|----------|------|----------|
| 4 | **UI 阻塞** | `ccviewer.cpp:1318-1368` | `runPythonScript()` 阻塞 UI 线程（`waitForFinished(120000)`），4个工具均受影响 | 大点云操作时 UI 冻结长达2分钟 | 改用 `QProcess::start()` + 信号槽异步模式 |
| 5 | **I/O 性能** | `ccviewer.cpp:1370-1396` | `exportSelectedCloudToCSV()` 逐点 `QTextStream <<` 写入，无批量缓冲 | 10M点云导出极慢且阻塞 UI | 使用 `QTextStream << QVector<QByteArray>` 批量写入或 `QSaveFile` |
| 6 | **启动延迟** | `ccviewer.cpp:1258-1316` | `resolvePythonExe()` 首次调用时探测4+次 QProcess，每次阻塞数秒 | 首次使用Python工具卡顿3-5秒 | 改为后台线程探测，或改用 `QStandardPaths::findExecutable` |
| 7 | **内存管理** | `ccviewer.h:239-241` | `m_glWindow`、`m_selectedObject`、`m_3dMouseInput`、`m_clipBox` 等全部为裸指针，无智能指针 | 析构路径遗漏即泄漏 | 关键拥有指针改为 `std::unique_ptr` |
| 8 | **内存管理** | `ccviewer.cpp:76` | `static ccCameraParamEditDlg* s_cpeDlg` 全局裸指针，手动 delete | 静态对象生命周期风险 | 改为 `std::unique_ptr` + 静态局部变量 |
| 9 | **场景加载** | `ccviewer.cpp:588-684` | `addToDB(QStringList)` 每次加载先删除整个场景 DB，再逐文件同步加载 | 多文件拖放时 UI 冻结，丢失视角状态 | 改为增量加载 + 进度对话框 |

---

## 四、P2 — 中优先级（代码质量/构建优化）

| # | 类别 | 文件:行 | 问题描述 | 建议方案 | 状态 |
|---|------|---------|----------|----------|------|
| 10 | **代码重复** | `ccviewer.cpp:1468-1836` | `doActionPointProjection()` (162行) 和 `doActionRotationMatrix()` (134行) 构建几乎相同的 QDialog | 提取 `createDoubleSpinBoxDialog()` 工具函数 | ⬜ 待做 |
| 11 | **代码重复** | `ccviewer.cpp:1402-1836` | JSON 解析+错误检查模式重复 3 次 | 提取 `parseJsonOrLogError()` 工具函数 | ⬜ 待做 |
| 12 | **代码重复** | `ccviewer.cpp:979-1048` | 4个处理对话框处理程序遵循完全相同的模板模式 | 提取通用模板辅助函数 | ⬜ 待做 |
| 13 | **构建系统** | `CMakeLists.txt:1` | `cmake_minimum_required(VERSION 3.10)` 过低，Qt6 要求 3.16+ | 改为 `VERSION 3.16` | ✅ 已修复 |
| 14 | **构建系统** | `CMakeSetCompilerOptions.cmake:20-23` | LTO 在多配置生成器（VS）上因检查 `CMAKE_BUILD_TYPE` 可能静默失效 | 改为 `check_ipo_supported()` | ✅ 已修复 |
| 15 | **废弃 API** | `main.cpp:51` | `Qt::AA_EnableHighDpiScaling` 在 Qt6 中已废弃（始终启用） | 删除此行 | ✅ 已修复 |
| 16 | **废弃 API** | `ccApplicationBase.cpp:88` | `Qt::AA_ShareOpenGLContexts` 在 Qt6 中已废弃 | 删除此行 | ⬜ 待做（上游代码，风险较高） |
| 17 | **构建系统** | `cmake/CMakeSetCompilerOptions.cmake:38` | `_SECURE_SCL=0` 禁用检查迭代器，掩盖迭代器 bug | 移除此定义 | ✅ 已修复 |

---

## 五、P3 — 低优先级（技术债务/清理）

| # | 类别 | 文件:行 | 问题描述 | 建议方案 | 状态 |
|---|------|---------|----------|----------|------|
| 18 | **死代码** | `ccviewer.cpp:1969-1970` | `on3DMouseKeyUp()` / `on3DMouseCMDKeyUp()` 为空方法体 | 清理或标记为保留 | ⬜ 待做 |
| 19 | **死代码** | `ccviewer.h:98-100` | `freezeUI(bool)` 空 override | 移除或实现 | ⬜ 待做 |
| 20 | **冗余代码** | `ccviewer.cpp:101` | `setStyleSheet(QString())` 紧跟 `setStyleSheet("...")` 第一次调用无意义 | 删除冗余调用 | ✅ 已修复 |
| 21 | **API 命名** | `FileIOFilter.cpp:166,171` | `ResetSesionCounter()` / `IncreaseSesionCounter()` 拼写错误（"Sesion"→"Session"） | 修正拼写（需同步改头文件） | ⬜ 待做 |
| 22 | **重复源码** | `libs/qCC_db/extern/CCCoreLib-master/` | 完整复制了 `CCCoreLib/` 目录，磁盘浪费且易混淆 | 删除 `CCCoreLib-master/` | ⬜ 待做 |

---

## 六、大型文件拆分建议

| 文件 | 行数 | 大小 | 拆分建议 |
|------|------|------|----------|
| `ccGLWindowInterface.cpp` | 7,308 | 212KB | 拆分为渲染/交互/摄像机模块 |
| `ccPointCloud.cpp` | 7,192 | 201KB | 拆分为数据/渲染/IO 模块 |
| `ccviewer.cpp` | 2,021 | 69KB | 拆分为 `ccviewer_python.cpp`（Python工具）、`ccviewer_processing.cpp`（处理对话框）、`ccviewer_main.cpp`（UI/核心） |

---

## 七、日志系统分析（为"保存日志文件"功能准备）

### 现状
- `ccViewerLog`（[ccviewerlog.h](ccViewer-slim-full/ccViewer/ccviewerlog.h)）仅在 `LOG_ERROR` 时弹 QMessageBox，其余级别消息**全部丢弃**
- 无文件日志能力，无消息备份
- `ccLog::EnableMessageBackup(true)` **从未被调用**，注册前的消息（如插件加载日志）全部丢失

### 建议方案：扩展 ccViewerLog

1. 添加 `QFile` + `QTextStream` 成员变量
2. 在构造函数中打开日志文件（路径: `<exeDir>/logs/ccViewer_YYYYMMDD_HHMMSS.log`）
3. 在 `logMessage()` 中格式化写入: `[时间戳] [级别] 消息内容`
4. 在 `main.cpp` 中调用 `ccLog::EnableMessageBackup(true)` 捕获启动阶段日志
5. 也在 `dispToConsole()` 中写入日志文件
6. 添加日志级别前缀映射: `VERBOSE→[V]`、`STANDARD→[S]`、`IMPORTANT→[I]`、`WARNING→[W]`、`ERROR→[E]`

---

## 八、实施路线图

### 第一阶段（1-2周）: 功能修复 + 日志
- [x] 实现日志文件保存功能（扩展 ccViewerLog）
- [x] 修复4个处理功能的空壳问题（P0 #1, #2）
- [x] 启用消息备份系统

### 第二阶段（2-3周）: 性能优化
- [ ] Python 工具改为异步 QProcess（P1 #4）
- [ ] CSV 导出批量写入优化（P1 #5）
- [ ] 场景增量加载（P1 #9）
- [ ] 智能指针替换关键裸指针（P1 #7, #8）

### 第三阶段（1-2周）: 代码质量
- [ ] 提取重复代码工具函数（P2 #10-12）
- [x] 构建系统更新（P2 #13-14, #17）
- [x] 清理废弃 API 调用（P2 #15）
- [x] 冗余代码清理（P3 #20）
- [ ] 死代码清理（P3 #18-19, #21-22）
