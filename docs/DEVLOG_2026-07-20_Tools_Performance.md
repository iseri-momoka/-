# 开发日志：Tools 菜单性能优化

> 日期: 2026-07-20 ~ 2026-07-21
> 仓库: https://github.com/iseri-momoka/-.git
> 分支: main

---

## 一、任务目标

用户反馈 Tools 菜单中的 8 个工具函数调用速度太慢，要求：
1. 加快执行速度
2. 为所有慢操作添加进度条

## 二、完成的优化

### 第一阶段：Python → C++ 原生实现 (commit b3aea25)

将 4 个 Python 工具改为 CCCoreLib 原生 C++ 实现，彻底消除 CSV 导出、子进程启动、JSON 解析三层开销。

| 工具 | 原实现 | 新实现 |
|------|--------|--------|
| TLS 平面拟合 | Python tls_plane.py | CCCoreLib::Neighbourhood::getLSPlane |
| 点投影 | Python point_projection.py | C++ 内存计算 |
| KNN 搜索 | Python knn_search.py | CCCoreLib::DgmOctree::findPointNeighbourhood |
| 旋转矩阵 | Python rotation_matrix.py | C++ Rodrigues 旋转公式 |

### 第二阶段：进度条 + 算法优化 (commit ab0772b)

#### 进度条 (6 个函数)
- doActionKNNSearch — ccProgressDialog + NormalizedProgress
- doActionPointProjection — ccProgressDialog + NormalizedProgress
- doActionBoundaryExtract — ccProgressDialog 传入 boundaryExtract()
- doActionFoldExtract — ccProgressDialog 传入 foldExtract()
- doActionSphereNeighborhood — ccProgressDialog 传入 sphereNeighborhoodExtract()
- doActionSpherePCA — ccProgressDialog 传入 spherePCACompute()

#### 算法性能优化

**边界点提取 (boundaryExtract)**
- 复用 ReferenceCloud 跨迭代，消除每次迭代的分配开销
- Octree 构建阶段添加进度回调

**折叠点提取 (foldExtract)**
- 直接调用 octree.getPointsInSphericalNeighbourhood() 替代 sphereNeighbors() 辅助函数
- 复用 NeighboursSet 跨迭代
- 搜索和检测阶段分别添加进度条

**球邻域提取 (sphereNeighborhoodExtract)**
- 直接调用 octree.getPointsInSphericalNeighbourhood() 替代 sphereNeighbors() 辅助函数
- 复用 NeighboursSet 跨迭代

**球 PCA 法线 (spherePCACompute)**
- 直接调用 octree.getPointsInSphericalNeighbourhood() 替代 sphereNeighbors() 辅助函数
- 复用 NeighboursSet 和 neighborIndices 跨迭代
- Octree 构建阶段添加进度回调

## 三、修改的文件

| 文件 | 变更 |
|------|------|
| ccViewer/ccviewer.cpp | 6 个工具函数添加进度条 |
| ccViewer/ccViewerAlgorithms.cpp | 4 个算法函数性能优化 |
| ccViewer/ccViewerAlgorithms.h | 无变更（仅保留） |

## 四、构建验证

- 构建配置: Release (cmake --preset slim)
- 构建结果: 成功 (ccViewer.exe 365KB)
- 链接: 成功，无编译错误

## 五、提交记录

```
ab0772b perf: add progress bars and optimize algorithm performance for Tools menu
b3aea25 refactor: replace Python tool algorithms with native C++ CCCoreLib implementations
```

## 六、未来可进一步优化

1. 八叉树预缓存 — 在 ccViewer 中维护一个八叉树缓存，多个工具共享使用
2. 并行处理 — 使用 QtConcurrent::map 替代串行循环（需检查 CCCORELIB_USE_QT_CONCURRENT）
3. 场景增量加载 — P1 #9 问题：多文件拖放时 UI 冻结
