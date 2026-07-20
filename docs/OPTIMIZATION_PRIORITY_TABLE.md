# ccViewer Slim — 优化优先级表

> 生成日期: 2026-07-20
> 范围: `ccViewer-full/` 全代码库

---

## 一、优化总览

| 优先级 | 类别 | 数量 | 状态摘要 |
|--------|------|------|----------|
| **P0 — 必须** | 功能缺陷/数据安全 | 3 | 3/3 已修复 ✅ |
| **P1 — 高** | 性能瓶颈 | 6 | 0/6 已修复 |
| **P2 — 中** | 代码质量/构建优化 | 8 | 5/8 已修复 ✅ |
| **P3 — 低** | 技术债务/清理 | 5 | 1/5 已修复 |

---

## 二、P0 — 必须修复（功能缺陷/数据安全）

| # | 问题 | 文件:行 | 描述 | 影响 | 状态 |
|---|------|---------|------|------|------|
| 1 | 处理功能空壳 | `ccviewer.cpp:1020-1230` | 4个处理对话框仅弹窗不执行计算 | 法线/子采样/过滤/SOR 全不可用 | ✅ 已修复 |
| 2 | 按值过滤无操作 | `ccviewer.cpp:1092-1166` | `doActionFilterByValue()` 读参数后无过滤 | 过滤功能为空壳 | ✅ 已修复 |
| 3 | QProcess 路径注入 | `ccviewer.cpp:1578-1642` | `runPythonScript()` 路径直接传 QProcess | 潜在注入风险 | ⏭ 无需修复（QProcess::start 不经 shell）|

---

## 三、P1 — 高优先级（性能瓶颈）

| # | 问题 | 文件:行 | 描述 | 影响 | 建议方案 | 状态 |
|---|------|---------|------|------|----------|------|
| 4 | **UI 阻塞** | `ccviewer.cpp:1578-1642` | `runPythonScript()` 使用 `waitForFinished(120000)` 同步等待 | 4个Python工具 UI 冻结最长2分钟 | 改用信号槽异步 `QProcess::start()` | ⬜ 待做 |
| 5 | **I/O 性能** | `ccviewer.cpp:1370-1396` | `exportSelectedCloudToCSV()` 逐点 `QTextStream <<` 写入 | 10M+ 点云导出极慢且阻塞 UI | 批量写入 `QVector<QByteArray>` 或 `QSaveFile` | ⬜ 待做 |
| 6 | **启动延迟** | `ccviewer.cpp:1258-1316` | `resolvePythonExe()` 同步探测 4+ 次 QProcess | 首次使用 Python 工具卡顿 3-5秒 | 后台线程探测或 `QStandardPaths::findExecutable` | ⬜ 待做 |
| 7 | **内存管理** | `ccviewer.h:239-241` | `m_glWindow`、`m_selectedObject` 等裸指针 | 析构路径遗漏即泄漏 | 关键拥有指针改为 `std::unique_ptr` | ⬜ 待做 |
| 8 | **内存管理** | `ccviewer.cpp:76` | `static ccCameraParamEditDlg* s_cpeDlg` 全局裸指针 | 静态对象生命周期风险 | `std::unique_ptr` + 静态局部变量 | ⬜ 待做 |
| 9 | **场景加载** | `ccviewer.cpp:588-684` | `addToDB(QStringList)` 先删整个 DB 再逐文件同步加载 | 多文件拖放 UI 冻结，丢失视角 | 增量加载 + 进度对话框 | ⬜ 待做 |

---

## 四、P2 — 中优先级（代码质量/构建优化）

| # | 问题 | 文件:行 | 描述 | 建议方案 | 状态 |
|---|------|---------|------|----------|------|
| 10 | **代码重复** | `ccviewer.cpp:1644-1920` | `doActionPointProjection()` (162行) 与 `doActionRotationMatrix()` (134行) 构建几乎相同的 QDialog | 提取 `createDoubleSpinBoxDialog()` 工具函数 | ⬜ 待做 |
| 11 | **代码重复** | `ccviewer.cpp:1578-1920` | JSON 解析 + 错误检查模式重复 3 次 | 提取 `parseJsonOrLogError()` 工具函数 | ⬜ 待做 |
| 12 | **代码重复** | `ccviewer.cpp:1020-1230` | 4个处理对话框遵循完全相同的模板模式 | 提取通用模板辅助函数 | ⬜ 待做 |
| 13 | **CMake版本过低** | `CMakeLists.txt:1` | `cmake_minimum_required(VERSION 3.10)`，Qt6 要求 3.16+ | 改为 `VERSION 3.16` | ✅ 已修复 |
| 14 | **LTO配置失效** | `cmake/CMakeSetCompilerOptions.cmake:20-23` | VS 多配置生成器上因检查 `CMAKE_BUILD_TYPE` 可能静默失效 | 改用 `check_ipo_supported()` | ✅ 已修复 |
| 15 | **废弃API** | `main.cpp:51` | `Qt::AA_EnableHighDpiScaling` 在 Qt6 中已废弃 | 删除此行 | ✅ 已修复 |
| 16 | **废弃API** | `ccApplicationBase.cpp:88` | `Qt::AA_ShareOpenGLContexts` 在 Qt6 中已废弃 | 删除此行（上游代码，风险较高） | ⬜ 待做 |
| 17 | **迭代器检查禁用** | `cmake/CMakeSetCompilerOptions.cmake:38` | `_SECURE_SCL=0` 禁用检查迭代器，掩盖 bug | 移除此定义 | ✅ 已修复 |

---

## 五、P3 — 低优先级（技术债务/清理）

| # | 问题 | 文件:行 | 描述 | 建议方案 | 状态 |
|---|------|---------|------|----------|------|
| 18 | **死代码** | `ccviewer.cpp:1969-1970` | `on3DMouseKeyUp()` / `on3DMouseCMDKeyUp()` 空方法体 | 清理或标记为保留 | ⬜ 待做 |
| 19 | **死代码** | `ccviewer.h:98-100` | `freezeUI(bool)` 空 override | 移除或实现 | ⬜ 待做 |
| 20 | **冗余代码** | `ccviewer.cpp:101` | `setStyleSheet(QString())` 紧跟有效调用 | 删除冗余调用 | ✅ 已修复 |
| 21 | **拼写错误** | `FileIOFilter.cpp:166,171` | `ResetSesionCounter()` / `IncreaseSesionCounter()` | "Sesion"→"Session"（需同步头文件） | ⬜ 待做 |
| 22 | **重复源码** | `libs/qCC_db/extern/CCCoreLib-master/` | 完整复制了 `CCCoreLib/` 目录 | 删除 `CCCoreLib-master/` 目录 | ⬜ 待做 |

---

## 六、大型文件拆分建议

| 文件 | 行数 | 大小 | 拆分建议 |
|------|------|------|----------|
| `ccviewer.cpp` | 2,536 | ~69KB | 拆为 `ccviewer_python.cpp`（Python工具）、`ccviewer_processing.cpp`（处理对话框）、`ccviewer_main.cpp`（UI/核心） |
| `ccGLWindowInterface.cpp` | 7,308 | ~212KB | 拆为渲染/交互/摄像机模块（上游代码，高风险） |
| `ccPointCloud.cpp` | 7,192 | ~201KB | 拆为数据/渲染/IO模块（上游代码，高风险） |

---

## 七、日志系统改进

| 优先级 | 问题 | 描述 | 建议 |
|--------|------|------|------|
| **中** | 无文件日志 | `ccViewerLog` 仅弹 QMessageBox，其余消息丢弃 | 扩展为文件日志器（路径: `<exeDir>/logs/`）|
| **中** | 启动日志丢失 | `ccLog::EnableMessageBackup(true)` 未调用，插件加载日志丢失 | 在 `main.cpp` 中启用 |
| **低** | 无日志级别映射 | 当前只有 ERROR 有弹窗 | 添加 V/S/I/W/E 级别前缀 |

---

## 八、实施路线图

### 第一阶段（已全部完成 ✅）
- [x] 实现日志文件保存功能（扩展 ccViewerLog）
- [x] 修复4个处理功能的空壳问题（P0 #1, #2）
- [x] 启用消息备份系统
- [x] 构建系统更新（P2 #13-14, #17）
- [x] 清理废弃 API 调用（P2 #15）
- [x] 冗余代码清理（P3 #20）

### 第二阶段（2-3周）: 性能优化
- [ ] Python 工具改为异步 QProcess（P1 #4）
- [ ] CSV 导出批量写入优化（P1 #5）
- [ ] 场景增量加载（P1 #9）
- [ ] 智能指针替换关键裸指针（P1 #7, #8）
- [ ] 后台线程 Python 路径探测（P1 #6）

### 第三阶段（1-2周）: 代码质量
- [ ] 提取重复代码工具函数（P2 #10-12）
- [ ] 死代码清理（P3 #18-19, #21-22）
- [ ] 废弃 API 清理（P2 #16）
- [ ] 大型文件拆分（见第六节）

---

## 九、待接入的 qCC 对话框（4个）

| 对话框 | 文件 | 依赖 | 复杂度 | 备注 |
|--------|------|------|--------|------|
| ccComparisonDlg | `qCC_selected/dialogs/ccComparisonDlg.h/.cpp` | ccOctree, ccPointCloud | 中 | 云/云、云/ mesh 距离比较 |
| ccRegistrationDlg | `qCC_selected/dialogs/ccRegistrationDlg.h/.cpp` | 点云配准算法 | 高 | ICP 等配准功能 |
| ccAlignDlg | `qCC_selected/dialogs/ccAlignDlg.h/.cpp` | 点云对齐 | 高 | 粗对齐/精对齐 |
| ccGraphicalSegmentationTool | `qCC_selected/dialogs/ccGraphicalSegmentationTool.h/.cpp` | 图形分割 | 中 | 交互式区域分割 |
