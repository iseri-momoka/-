# CloudCompare 前端源代码分析报告

## 1. 源代码整体结构

```
CloudCompare-master/
├── qCC/                    # ★ 前端主程序（Qt/C++）
│   ├── mainwindow.h/.cpp   # 主窗口类（2700+ 行）
│   ├── main.cpp            # 入口
│   └── cc*.h/.cpp          # 各种对话框和工具（80+ 文件）
│
├── libs/
│   ├── qCC_db/             # 数据模型层（ccPointCloud/ccMesh/ccHObject 等）
│   ├── CCFbo/              # FBO 渲染（帧缓冲对象）
│   ├── CCAppCommon/        # 公共应用组件（显示设置、插件管理等）
│   ├── CCPluginAPI/        # 插件 API 接口
│   └── CCPluginStub/       # 插件桩
│
├── plugins/                # 标准插件（滤波/配准/分割等）
│   ├── standard/
│   └── qPOI/
│
└── ccViewer/               # 轻量查看器（不含编辑功能）
```

---

## 2. 主窗口 MainWindow（核心文件）

**文件**: `qCC/mainwindow.h` + `qCC/mainwindow.cpp`（~2700 行）

**继承**: `QMainWindow` + `ccMainAppInterface` + `ccPickingListener`

### 核心成员变量

| 成员 | 类型 | 作用 |
|---|---|---|
| `m_UI` | `Ui::MainWindow*` | Qt Designer 生成的 UI |
| `m_ccRoot` | `ccDBRoot*` | 数据库树根节点 |
| `m_selectedEntities` | `ccHObject::Container` | 当前选中的实体列表 |
| `m_mdiArea` | `QMdiArea*` | 多文档界面区域（3D 视口容器） |
| `m_recentFiles` | `ccRecentFiles*` | 最近打开文件列表 |
| `m_pickingHub` | `ccPickingHub*` | 点拾取管理中心 |
| `m_pluginUIManager` | `ccPluginUIManager*` | 插件 UI 管理器 |

### 对话框/工具实例

| 成员 | 类型 | 功能 |
|---|---|---|
| `m_cpeDlg` | `ccCameraParamEditDlg` | 相机参数编辑 |
| `m_gsTool` | `ccGraphicalSegmentationTool` | 图形分割工具 |
| `m_tplTool` | `ccTracePolylineTool` | 折线跟踪工具 |
| `m_seTool` | `ccSectionExtractionTool` | 截面提取工具 |
| `m_transTool` | `ccGraphicalTransformationTool` | 图形平移/旋转 |
| `m_clipTool` | `ccClippingBoxTool` | 裁剪盒工具 |
| `m_compDlg` | `ccComparisonDlg` | 实体距离对比 |
| `m_ppDlg` | `ccPointPropertiesDlg` | 点属性查看 |
| `m_plpDlg` | `ccPointListPickingDlg` | 点列表拾取 |
| `m_pprDlg` | `ccPointPairRegistrationDlg` | 点对配准 |
| `m_pfDlg` | `ccPrimitiveFactoryDlg` | 图元工厂（创建平面/球等） |

---

## 3. 功能 → 代码段完整映射

### 3.1 File 菜单

| 功能 | 方法 | 对话框类 | 文件 |
|---|---|---|---|
| 打开文件 | `doActionLoadFile()` | — | `mainwindow.cpp` |
| 保存文件 | `doActionSaveFile()` | — | `mainwindow.cpp` |
| 保存项目 | `doActionSaveProject()` | — | `mainwindow.cpp` |
| 导出到文件 | `doActionRenderToFile()` | `ccRenderToFileDlg` | `CCPluginAPI/include/ccRenderToFileDlg.h` |
| 全局偏移设置 | `doActionGlobalShiftSeetings()` | — | `mainwindow.cpp` |
| 最近文件 | `m_recentFiles` | — | `qCC/ccRecentFiles.h` |
| 关闭全部 | `closeAll()` | — | `mainwindow.cpp` |

### 3.2 Edit 菜单

| 功能 | 方法 | 文件 |
|---|---|---|
| 克隆实体 | `doActionClone()` | `mainwindow.cpp` |
| 合并实体 | `doActionMerge()` | `mainwindow.cpp` |
| 应用变换 | `doActionApplyTransformation()` | `ccApplyTransformationDlg.h/.cpp` |
| 裁剪 | `doActionCrop()` | `ccCropTool.h/.cpp` |
| 编辑全局偏移/缩放 | `doActionEditGlobalShiftAndScale()` | `mainwindow.cpp` |
| 应用缩放 | `doActionApplyScale()` | `mainwindow.cpp` |

### 3.3 View 菜单（13 个标准视角）

| 功能 | 方法 | 文件 |
|---|---|---|
| 13 个视角预设 | `setView(CC_VIEW_ORIENTATION)` | `mainwindow.cpp` |
| 正交/透视切换 | `setOrthoView()` / `setCenteredPerspectiveView()` / `setViewerPerspectiveView()` | `mainwindow.cpp` |
| 全局缩放 | `setGlobalZoom()` | `mainwindow.cpp` |
| 缩放到选中 | `zoomOnSelectedEntities()` | `mainwindow.cpp` |
| 放大/缩小 | `zoomIn()` / `zoomOut()` | `mainwindow.cpp` |
| 点大小增减 | `increasePointSize()` / `decreasePointSize()` | `mainwindow.cpp` |
| 全屏 | `toggleFullScreen()` | `mainwindow.cpp` |
| 独占全屏 | `toggleExclusiveFullScreen()` | `mainwindow.cpp` |
| 显示设置 | `showDisplaySettings()` | `ccDisplaySettingsDlg.h` (CCAppCommon) |
| 相机参数编辑 | `doActionEditCamera()` | `ccCameraParamEditDlg.h` (CCAppCommon) |
| 调整缩放 | `doActionAdjustZoom()` | `ccAdjustZoomDlg.h/.cpp` |
| 保存视口为相机 | `doActionSaveViewportAsCamera()` | `mainwindow.cpp` |
| 重置 GUI 位置 | `doActionResetGUIElementsPos()` | `mainwindow.cpp` |
| 立体视觉 | `toggleActiveWindowStereoVision()` | `ccStereoModeDlg.h` (CCAppCommon) |
| 自定义光/太阳光 | `toggleActiveWindowCustomLight()` / `toggleActiveWindowSunLight()` | `mainwindow.cpp` |
| 锁定旋转轴 | `toggleLockRotationAxis()` | `mainwindow.cpp` |
| Pivot 显示 | `setPivotAlwaysOn()` / `setPivotRotationOnly()` / `setPivotOff()` | `mainwindow.cpp` |
| 坐标显示 | `toggleActiveWindowShowCursorCoords()` | `mainwindow.cpp` |
| 气泡视图 | `doActionEnableBubbleViewMode()` | `mainwindow.cpp` |

### 3.4 Tools 菜单

| 功能 | 方法 | 对话框类 | 文件 |
|---|---|---|---|
| **图形分割** | `activateSegmentationMode()` | `ccGraphicalSegmentationTool` | `qCC/ccGraphicalSegmentationTool.h/.cpp` |
| **图形变换** | `activateTranslateRotateMode()` | `ccGraphicalTransformationTool` | `qCC/ccGraphicalTransformationTool.h/.cpp` |
| **裁剪盒** | `activateClippingBoxMode()` | `ccClippingBoxTool` | `qCC/ccClippingBoxTool.h/.cpp` |
| **折线跟踪** | `activateTracePolylineMode()` | `ccTracePolylineTool` | `qCC/ccTracePolylineTool.h/.cpp` |
| **截面提取** | `activateSectionExtractionMode()` | `ccSectionExtractionTool` | `qCC/ccSectionExtractionTool.h/.cpp` |
| **点拾取** | `activatePointPickingMode()` | `ccPointPropertiesDlg` | `qCC/ccPointPropertiesDlg.h/.cpp` |
| **点列表拾取** | `activatePointListPickingMode()` | `ccPointListPickingDlg` | `qCC/ccPointListPickingDlg.h/.cpp` |
| **点对配准** | `activateRegisterPointPairTool()` | `ccPointPairRegistrationDlg` | `qCC/ccPointPairRegistrationDlg.h/.cpp` |
| **图元工厂** | `doShowPrimitiveFactory()` | `ccPrimitiveFactoryDlg` | `qCC/ccPrimitiveFactoryDlg.h/.cpp` |
| 距离对比（Cloud-Cloud） | `doActionCloudCloudDist()` | `ccComparisonDlg` | `qCC/ccComparisonDlg.h/.cpp` |
| 距离对比（Cloud-Mesh） | `doActionCloudMeshDist()` | `ccComparisonDlg` | 同上 |
| 距离对比（Cloud-Primitive） | `doActionCloudPrimitiveDist()` | `ccComparisonDlg` | 同上 |
| 实体统计 | `doActionComputeStatParams()` | — | `mainwindow.cpp` |
| 按值筛选 | `doActionFilterByValue()` | `ccFilterByValueDlg` | `qCC/ccFilterByValueDlg.h/.cpp` |

### 3.5 Cloud 操作（Tools → Cloud）

| 功能 | 方法 | 对话框类 | 文件 |
|---|---|---|---|
| 法向量计算 | `doActionComputeNormals()` | `ccNormalComputationDlg` | `qCC/ccNormalComputationDlg.h/.cpp` |
| 反转法向量 | `doActionInvertNormals()` | — | `mainwindow.cpp` |
| 法向量→HSV | `doActionConvertNormalsToHSV()` | — | `mainwindow.cpp` |
| 法向量→倾角/倾向 | `doActionConvertNormalsToDipDir()` | — | `mainwindow.cpp` |
| 法向量定向（FM） | `doActionOrientNormalsFM()` | — | `mainwindow.cpp` |
| 法向量定向（MST） | `doActionOrientNormalsMST()` | — | `mainwindow.cpp` |
| 沿法向量移动点 | `doActionShiftPointsAlongNormals()` | — | `mainwindow.cpp` |
| Octree 计算 | `doActionComputeOctree()` | `ccComputeOctreeDlg` | `qCC/ccComputeOctreeDlg.h/.cpp` |
| KDTree 计算 | `doActionComputeKdTree()` | — | `mainwindow.cpp` |
| 体素降采样 | `doActionSubsample()` | `ccSubsamplingDlg` | `qCC/ccSubsamplingDlg.h/.cpp` |
| SOR 滤波 | `doActionSORFilter()` | `ccSORFilterDlg` | `qCC/ccSORFilterDlg.h/.cpp` |
| 噪声滤波 | `doActionFilterNoise()` | `ccNoiseFilterDlg` | `qCC/ccNoiseFilterDlg.h/.cpp` |
| 统计检验 | `doActionStatisticalTest()` | `ccStatisticalTestDlg` | `qCC/ccStatisticalTestDlg.h/.cpp` |
| 标量场算术 | `doActionScalarFieldArithmetic()` | `ccScalarFieldArithmeticsDlg` | `qCC/ccScalarFieldArithmeticsDlg.h/.cpp` |
| 标量场→RGB | `doActionSFConvertToRGB()` | — | `mainwindow.cpp` |
| 标量场梯度 | `doActionSFGradient()` | — | `mainwindow.cpp` |
| 分割组件 | `doActionLabelConnectedComponents()` | — | `mainwindow.cpp` |
| 重采样（Octree） | `doActionResampleWithOctree()` | — | `mainwindow.cpp` |
| 删除重复点 | `doActionRemoveDuplicatePoints()` | — | `mainwindow.cpp` |
| KMeans 聚类 | `doActionKMeans()` | — | `mainwindow.cpp` |
| 前向传播分割 | `doActionFrontPropagation()` | — | `mainwindow.cpp` |
| 球面邻域测试 | `doSphericalNeighbourhoodExtractionTest()` | — | `mainwindow.cpp` |
| 圆柱邻域测试 | `doCylindricalNeighbourhoodExtractionTest()` | — | `mainwindow.cpp` |
| 坐标→标量场 | `doActionExportCoordToSF()` | `ccExportCoordToSFDlg` | `qCC/ccExportCoordToSFDlg.h/.cpp` |
| 法向量→标量场 | `doActionExportNormalToSF()` | — | `mainwindow.cpp` |
| 从颜色提取标量 | `doActionScalarFieldFromColor()` | `ccScalarFieldFromColorDlg` | `qCC/ccScalarFieldFromColorDlg.h/.cpp` |
| 平滑折线 | `doActionSmoohPolyline()` | `ccSmoothPolylineDlg` | `qCC/ccSmoothPolylineDlg.h/.cpp` |
| 在网格上采样点 | `doActionSamplePointsOnMesh()` | `ccPtsSamplingDlg` | `qCC/ccPtsSamplingDlg.h/.cpp` |
| 在折线上采样点 | `doActionSamplePointsOnPolyline()` | `ccPtsSamplingDlg` | 同上 |
| 展开 | `doActionUnroll()` | `ccUnrollDlg` | `qCC/ccUnrollDlg.h/.cpp` |
| 展开为圆柱 | `doActionPromoteCircleToCylinder()` | — | `mainwindow.cpp` |

### 3.6 几何拟合（Tools → Fit）

| 功能 | 方法 | 对话框类 | 文件 |
|---|---|---|---|
| 拟合平面 | `doActionFitPlane()` | — | `mainwindow.cpp` |
| 拟合球 | `doActionFitSphere()` | `ccFitSphereDlg` | `qCC/ccFitSphereDlg.h/.cpp` |
| 拟合圆 | `doActionFitCircle()` | — | `mainwindow.cpp` |
| 拟合 Facet | `doActionFitFacet()` | — | `mainwindow.cpp` |
| 拟合二次曲面 | `doActionFitQuadric()` | — | `mainwindow.cpp` |
| 几何特征计算 | `doComputeGeometricFeature()` | `ccGeomFeaturesDlg` | `qCC/ccGeomFeaturesDlg.h/.cpp` |
| 最优拟合 BB | `doComputeBestFitBB()` | — | `mainwindow.cpp` |
| 查找最大内接矩形 | `doActionFindBiggestInnerRectangle()` | — | `mainwindow.cpp` |

### 3.7 Mesh 操作（Tools → Mesh）

| 功能 | 方法 | 文件 |
|---|---|---|
| 计算网格（Alpha Shape） | `doActionComputeMeshAA()` | `mainwindow.cpp` |
| 计算网格（最小二乘） | `doActionComputeMeshLS()` | `mainwindow.cpp` |
| 网格扫描格 | `doActionMeshScanGrids()` | `mainwindow.cpp` |
| 计算距离图 | `doActionComputeDistanceMap()` | `mainwindow.cpp` |
| 计算到二次曲面距离 | `doActionComputeDistToBestFitQuadric3D()` | `mainwindow.cpp` |
| 测量网格表面积 | `doActionMeasureMeshSurface()` | `mainwindow.cpp` |
| 测量网格体积 | `doActionMeasureMeshVolume()` | `mainwindow.cpp` |
| 标记网格顶点 | `doActionFlagMeshVertices()` | `mainwindow.cpp` |
| 拉普拉斯平滑网格 | `doActionSmoothMeshLaplacian()` | `mainwindow.cpp` |
| 平滑网格标量场 | `doActionSmoothMeshSF()` | `mainwindow.cpp` |
| 增强网格标量场 | `doActionEnhanceMeshSF()` | `mainwindow.cpp` |
| 细分网格 | `doActionSubdivideMesh()` | `mainwindow.cpp` |
| 翻转三角面 | `doActionFlipMeshTriangles()` | `mainwindow.cpp` |
| 折线→网格 | `doConvertPolylinesToMesh()` | `mainwindow.cpp` |
| 两条折线→网格 | `doMeshTwoPolylines()` | `mainwindow.cpp` |
| 计算 CPS | `doActionComputeCPS()` | `mainwindow.cpp` |
| 2.5D 体积 | `doCompute2HalfDimVolume()` | `cc2.5DimEditor.h/.cpp` |

### 3.8 颜色操作（Edit → Colors）

| 功能 | 方法 | 对话框类 | 文件 |
|---|---|---|---|
| 设置唯一颜色 | `doActionSetUniqueColor()` | — | `mainwindow.cpp` |
| 着色 | `doActionColorize()` | — | `mainwindow.cpp` |
| RGB→灰度 | `doActionRGBToGreyScale()` | — | `mainwindow.cpp` |
| 设置颜色 | `doActionSetColor()` | — | `mainwindow.cpp` |
| 颜色渐变 | `doActionSetColorGradient()` | `ccColorGradientDlg` | `qCC/ccColorGradientDlg.h/.cpp` |
| 插值颜色 | `doActionInterpolateColors()` | — | `mainwindow.cpp` |
| 颜色级别 | `doActionChangeColorLevels()` | `ccColorLevelsDlg` | `qCC/ccColorLevelsDlg.h/.cpp` |
| RGB 增强 | `doActionEnhanceRGBWithIntensities()` | — | `mainwindow.cpp` |
| 标量场→颜色 | `doActionColorFromScalars()` | `ccColorFromScalarDlg` | `qCC/ccColorFromScalarDlg.h/.cpp` |
| RGB 高斯滤波 | `doActionRGBGaussianFilter()` | — | `mainwindow.cpp` |
| RGB 双边滤波 | `doActionRGBBilateralFilter()` | — | `mainwindow.cpp` |
| RGB 均值滤波 | `doActionRGBMeanFilter()` | — | `mainwindow.cpp` |
| RGB 中值滤波 | `doActionRGBMedianFilter()` | — | `mainwindow.cpp` |
| SF 高斯滤波 | `doActionSFGaussianFilter()` | — | `mainwindow.cpp` |
| SF 双边滤波 | `doActionSFBilateralFilter()` | — | `mainwindow.cpp` |
| SF→RGB | `doActionSFConvertToRGB()` | — | `mainwindow.cpp` |
| SF→随机 RGB | `doActionSFConvertToRandomRGB()` | — | `mainwindow.cpp` |
| 重命名 SF | `doActionRenameSF()` | — | `mainwindow.cpp` |
| 颜色管理器 | `doActionOpenColorScalesManager()` | — | `mainwindow.cpp` |
| 添加 ID 字段 | `doActionAddIdField()` | — | `mainwindow.cpp` |
| SF 分割云 | `doActionSplitCloudUsingSF()` | — | `mainwindow.cpp` |
| SF 作为坐标 | `doActionSetSFAsCoord()` | — | `mainwindow.cpp` |
| 插值标量场 | `doActionInterpolateScalarFields()` | `ccInterpolationDlg` | `qCC/ccInterpolationDlg.h/.cpp` |

### 3.9 配准（Tools → Registration）

| 功能 | 方法 | 对话框类 | 文件 |
|---|---|---|---|
| ICP 配准 | `doActionRegister()` | `ccRegistrationDlg` | `qCC/ccRegistrationDlg.h/.cpp` |
| 4PCS 配准 | `doAction4pcsRegister()` | — | `mainwindow.cpp` |
| 点对配准 | `activateRegisterPointPairTool()` | `ccPointPairRegistrationDlg` | `qCC/ccPointPairRegistrationDlg.h/.cpp` |
| 计算最佳 ICP RMS 矩阵 | `doActionComputeBestICPRmsMatrix()` | — | `mainwindow.cpp` |
| 匹配包围盒中心 | `doActionMatchBBCenters()` | — | `mainwindow.cpp` |
| 匹配缩放 | `doActionMatchScales()` | `ccMatchScalesDlg` | `qCC/ccMatchScalesDlg.h/.cpp` |
| 快速对齐到原点 | `doActionFastRegistration()` | — | `mainwindow.cpp` |

### 3.10 传感器（Tools → Sensor）

| 功能 | 方法 | 对话框类 | 文件 |
|---|---|---|---|
| 创建 GBL 传感器 | `doActionCreateGBLSensor()` | `ccGBLSensorProjectionDlg` | `qCC/ccGBLSensorProjectionDlg.h/.cpp` |
| 创建相机传感器 | `doActionCreateCameraSensor()` | `ccCamSensorProjectionDlg` | `qCC/ccCamSensorProjectionDlg.h/.cpp` |
| 修改传感器 | `doActionModifySensor()` | — | `mainwindow.cpp` |
| 投影不确定性 | `doActionProjectUncertainty()` | — | `mainwindow.cpp` |
| 检查视锥内点 | `doActionCheckPointsInsideFrustum()` | — | `mainwindow.cpp` |
| 计算到传感器距离 | `doActionComputeDistancesFromSensor()` | `ccSensorComputeDistancesDlg` | `qCC/ccSensorComputeDistancesDlg.h/.cpp` |
| 散射角计算 | `doActionComputeScatteringAngles()` | `ccSensorComputeScatteringAnglesDlg` | `qCC/ccSensorComputeScatteringAnglesDlg.h/.cpp` |
| 从传感器设置视图 | `doActionSetViewFromSensor()` | — | `mainwindow.cpp` |
| 深度缓冲查看 | `doActionShowDepthBuffer()` | — | `mainwindow.cpp` |
| 深度缓冲导出 | `doActionExportDepthBuffer()` | — | `mainwindow.cpp` |
| 可见性计算 | `doActionComputePointsVisibility()` | — | `mainwindow.cpp` |

### 3.11 栅格化（Tools → Raster）

| 功能 | 方法 | 对话框类 | 文件 |
|---|---|---|---|
| 栅格化 | `doActionRasterize()` | `ccRasterizeTool` | `qCC/ccRasterizeTool.h/.cpp` |
| 等值线生成 | — | `ccContourLinesGenerator` | `qCC/ccContourLinesGenerator.h/.cpp` |
| 等值线头文件 | — | `ccIsolines` | `qCC/ccIsolines.h` |
| 包络提取 | — | `ccEnvelopeExtractor` / `ccEnvelopeExtractorDlg` | `qCC/ccEnvelopeExtractor.h/.cpp` |
| 内接矩形查找 | — | `ccInnerRect2DFinder` | `qCC/ccInnerRect2DFinder.h/.cpp` |

### 3.12 插件系统

| 功能 | 类 | 文件 |
|---|---|---|
| 插件接口 | `ccPluginInterface` | `libs/CCPluginStub/include/ccPluginInterface.h` |
| 标准插件接口 | `ccStdPluginInterface` | `libs/CCPluginStub/include/ccStdPluginInterface.h` |
| IO 插件接口 | `ccIOPluginInterface` | `libs/CCPluginStub/include/ccIOPluginInterface.h` |
| GL 插件接口 | `ccGLPluginInterface` | `libs/CCPluginStub/include/ccGLPluginInterface.h` |
| 插件管理器 | `ccPluginManager` | `libs/CCAppCommon/include/ccPluginManager.h` |
| 主应用接口 | `ccMainAppInterface` | `libs/CCPluginAPI/include/ccMainAppInterface.h` |
| 拾取中心 | `ccPickingHub` | `libs/CCPluginAPI/include/ccPickingHub.h` |
| 叠加对话框 | `ccOverlayDialog` | `libs/CCPluginAPI/include/ccOverlayDialog.h` |
| 颜色管理 | `ccColorScaleEditorDlg` / `ccColorScaleSelector` | `libs/CCPluginAPI/include/` |

---

## 4. 数据模型层（libs/qCC_db）

| 类 | 文件 | 作用 |
|---|---|---|
| `ccHObject` | `libs/qCC_db/include/ccHObject.h` | **所有实体的基类**（层次结构） |
| `ccObject` | `libs/qCC_db/include/ccObject.h` | 对象基类（ID、名称、可见性） |
| `ccDrawableObject` | `libs/qCC_db/include/ccDrawableObject.h` | 可绘制对象接口 |
| `ccGenericPointCloud` | `libs/qCC_db/include/ccGenericPointCloud.h` | 点云基类 |
| `ccPointCloud` | `libs/qCC_db/include/ccPointCloud.h` | **点云实现**（坐标 + RGB + 法向量 + 标量场） |
| `ccGenericMesh` | `libs/qCC_db/include/ccGenericMesh.h` | 网格基类 |
| `ccMesh` | `libs/qCC_db/include/ccMesh.h` | **三角网格实现** |
| `ccSubMesh` | `libs/qCC_db/include/ccSubMesh.h` | 子网格（网格的子集） |
| `ccMeshGroup` | `libs/qCC_db/include/ccMeshGroup.h` | 网格组 |
| `ccPolyline` | `libs/qCC_db/include/ccPolyline.h` | 折线 |
| `ccScalarField` | `libs/qCC_db/include/ccScalarField.h` | **标量场数据** |
| `ccColorScale` | `libs/qCC_db/include/ccColorScale.h` | 颜色映射表 |
| `ccImage` | `libs/qCC_db/include/ccImage.h` | 图像数据 |
| `ccOctree` | `libs/qCC_db/include/ccOctree.h` | Octree |
| `ccKdTree` | `libs/qCC_db/include/ccKdTree.h` | KDTree |
| `ccBBox` | `libs/qCC_db/include/ccBBox.h` | 包围盒 |
| `ccGLMatrix` | `libs/qCC_db/include/ccGLMatrix.h` | 4x4 变换矩阵 |
| `ccMaterial` | `libs/qCC_db/include/ccMaterial.h` | 材质 |
| `ccSensor` | `libs/qCC_db/include/ccSensor.h` | 传感器基类 |
| `ccGBLSensor` | `libs/qCC_db/include/ccGBLSensor.h` | 地面激光扫描仪 |
| `ccCameraSensor` | `libs/qCC_db/include/ccCameraSensor.h` | 相机传感器 |
| `ccFacet` | `libs/qCC_db/include/ccFacet.h` | 多边形面片 |
| `ccPlane` | `libs/qCC_db/include/ccPlane.h` | 平面 |
| `ccSphere` | `libs/qCC_db/include/ccSphere.h` | 球 |
| `ccCylinder` | `libs/qCC_db/include/ccCylinder.h` | 圆柱 |
| `ccCone` | `libs/qCC_db/include/ccCone.h` | 圆锥 |
| `ccBox` | `libs/qCC_db/include/ccBox.h` | 长方体 |
| `ccTorus` | `libs/qCC_db/include/ccTorus.h` | 圆环 |
| `ccCircle` | `libs/qCC_db/include/ccCircle.h` | 圆 |
| `ccDisc` | `libs/qCC_db/include/ccDisc.h` | 圆盘 |
| `ccDish` | `libs/qCC_db/include/ccDish.h` | 碗状体 |
| `ccExtru` | `libs/qCC_db/include/ccExtru.h` | 拉伸体 |
| `ccQuadric` | `libs/qCC_db/include/ccQuadric.h` | 二次曲面 |
| `ccCoordinateSystem` | `libs/qCC_db/include/ccCoordinateSystem.h` | 坐标系 |
| `cc2DLabel` | `libs/qCC_db/include/cc2DLabel.h` | 2D 标签 |
| `ccClipBox` | `libs/qCC_db/include/ccClipBox.h` | 裁剪盒 |
| `ccDepthBuffer` | `libs/qCC_db/include/ccDepthBuffer.h` | 深度缓冲 |
| `ccRasterGrid` | `libs/qCC_db/include/ccRasterGrid.h` | 栅格网格 |

---

## 5. 公共组件层（libs/CCAppCommon）

| 类 | 文件 | 作用 |
|---|---|---|
| `ccDisplaySettingsDlg` | `libs/CCAppCommon/include/ccDisplaySettingsDlg.h` | 显示设置对话框 |
| `ccCameraParamEditDlg` | `libs/CCAppCommon/include/ccCameraParamEditDlg.h` | 相机参数编辑对话框 |
| `ccPluginManager` | `libs/CCAppCommon/include/ccPluginManager.h` | 插件管理器 |
| `ccStereoModeDlg` | `libs/CCAppCommon/include/ccStereoModeDlg.h` | 立体视觉对话框 |
| `ccOptions` | `libs/CCAppCommon/include/ccOptions.h` | 选项管理 |
| `ccTranslationManager` | `libs/CCAppCommon/include/ccTranslationManager.h` | 多语言翻译 |
| `cc3DMouseManager` | `libs/CCAppCommon/devices/3dConnexion/cc3DMouseManager.h` | 3D 鼠标管理 |

---

## 6. FBO 渲染层（libs/CCFbo）

| 类 | 文件 | 作用 |
|---|---|---|
| `ccFrameBufferObject` | `libs/CCFbo/include/ccFrameBufferObject.h` | FBO 帧缓冲 |
| `ccGlFilter` | `libs/CCFbo/include/ccGlFilter.h` | GL 滤镜基类 |
| `ccBilateralFilter` | `libs/CCFbo/include/ccBilateralFilter.h` | 双边滤波（GPU） |
| `ccShader` | `libs/CCFbo/include/ccShader.h` | Shader 管理 |
| `CCFbo` | `libs/CCFbo/include/CCFbo.h` | FBO 管理 |

---

## 7. 对话框类完整列表

| 对话框 | C++ 类 | 文件 | 功能 |
|---|---|---|---|
| 关于 | `ccAboutDialog` | `qCC/ccAboutDialog.h` | 软件信息 |
| 缩放调整 | `ccAdjustZoomDlg` | `qCC/ccAdjustZoomDlg.h` | 精确缩放 |
| 对齐 | `ccAlignDlg` | `qCC/ccAlignDlg.h` | 对齐工具 |
| 变换应用 | `ccApplyTransformationDlg` | `qCC/ccApplyTransformationDlg.h` | 应用 4x4 变换 |
| 三维数值输入 | `ccAskThreeDoubleValuesDlg` | `qCC/ccAskThreeDoubleValuesDlg.h` | 通用三维输入 |
| 二维数值输入 | `ccAskTwoDoubleValuesDlg` | `qCC/ccAskTwoDoubleValuesDlg.h` | 通用二维输入 |
| 包围盒编辑 | `ccBoundingBoxEditorDlg` | `qCC/ccBoundingBoxEditorDlg.h` | 编辑 BBox |
| 相机投影 | `ccCamSensorProjectionDlg` | `qCC/ccCamSensorProjectionDlg.h` | 相机投影设置 |
| 裁剪盒重复 | `ccClippingBoxRepeatDlg` | `qCC/ccClippingBoxRepeatDlg.h` | 裁剪盒重复 |
| 颜色渐变 | `ccColorGradientDlg` | `qCC/ccColorGradientDlg.h` | 颜色渐变设置 |
| 颜色级别 | `ccColorLevelsDlg` | `qCC/ccColorLevelsDlg.h` | 颜色级别调整 |
| 标量→颜色 | `ccColorFromScalarDlg` | `qCC/ccColorFromScalarDlg.h` | 标量映射颜色 |
| 对比 | `ccComparisonDlg` | `qCC/ccComparisonDlg.h` | 距离对比设置 |
| Octree 计算 | `ccComputeOctreeDlg` | `qCC/ccComputeOctreeDlg.h` | Octree 参数 |
| 裁剪 | `ccCropTool` | `qCC/ccCropTool.h` | 裁剪工具 |
| 实体选择 | `ccEntitySelectionDlg` | `qCC/ccEntitySelectionDlg.h` | 实体选择对话框 |
| 包络提取 | `ccEnvelopeExtractorDlg` | `qCC/ccEnvelopeExtractorDlg.h` | 包络参数 |
| 坐标→SF | `ccExportCoordToSFDlg` | `qCC/ccExportCoordToSFDlg.h` | 坐标导出为标量 |
| 按值筛选 | `ccFilterByValueDlg` | `qCC/ccFilterByValueDlg.h` | 标量值筛选 |
| 拟合球 | `ccFitSphereDlg` | `qCC/ccFitSphereDlg.h` | 球拟合参数 |
| GBL 传感器投影 | `ccGBLSensorProjectionDlg` | `qCC/ccGBLSensorProjectionDlg.h` | GBL 投影设置 |
| 几何特征 | `ccGeomFeaturesDlg` | `qCC/ccGeomFeaturesDlg.h` | 特征计算参数 |
| 图形分割选项 | `ccGraphicalSegmentationOptionsDlg` | `qCC/ccGraphicalSegmentationOptionsDlg.h` | 分割模式选项 |
| 直方图 | `ccHistogramWindow` | `qCC/ccHistogramWindow.h` | 标量场直方图 |
| 插值 | `ccInterpolationDlg` | `qCC/ccInterpolationDlg.h` | 标量场插值参数 |
| 项目选择 | `ccItemSelectionDlg` | `qCC/ccItemSelectionDlg.h` | 项目选择 |
| 克里金参数 | `ccKrigingParamsDialog` | `qCC/ccKrigingParamsDialog.h` | 克里金插值 |
| 标签 | `ccLabelingDlg` | `qCC/ccLabelingDlg.h` | 标签工具 |
| 缩放匹配 | `ccMatchScalesDlg` | `qCC/ccMatchScalesDlg.h` | 缩放匹配 |
| 噪声滤波 | `ccNoiseFilterDlg` | `qCC/ccNoiseFilterDlg.h` | 噪声参数 |
| 法向量计算 | `ccNormalComputationDlg` | `qCC/ccNormalComputationDlg.h` | 法向量参数 |
| 顺序选择 | `ccOrderChoiceDlg` | `qCC/ccOrderChoiceDlg.h` | 顺序选择 |
| 正交截面 | `ccOrthoSectionGenerationDlg` | `qCC/ccOrthoSectionGenerationDlg.h` | 正交截面 |
| 平面编辑 | `ccPlaneEditDlg` | `qCC/ccPlaneEditDlg.h` | 平面编辑 |
| 点列表拾取 | `ccPointListPickingDlg` | `qCC/ccPointListPickingDlg.h` | 点列表管理 |
| 点对配准 | `ccPointPairRegistrationDlg` | `qCC/ccPointPairRegistrationDlg.h` | 点对配准交互 |
| 点属性 | `ccPointPropertiesDlg` | `qCC/ccPointPropertiesDlg.h` | 点属性查看 |
| 图元距离 | `ccPrimitiveDistanceDlg` | `qCC/ccPrimitiveDistanceDlg.h` | 图元间距离 |
| 图元工厂 | `ccPrimitiveFactoryDlg` | `qCC/ccPrimitiveFactoryDlg.h` | 创建几何图元 |
| 采样点 | `ccPtsSamplingDlg` | `qCC/ccPtsSamplingDlg.h` | 采样参数 |
| 栅格化 | `ccRasterizeTool` | `qCC/ccRasterizeTool.h` | 栅格化工具 |
| 配准 | `ccRegistrationDlg` | `qCC/ccRegistrationDlg.h` | 配准参数 |
| 配准工具 | `ccRegistrationTools` | `qCC/ccRegistrationTools.h` | 配准工具类 |
| SF 算术 | `ccScalarFieldArithmeticsDlg` | `qCC/ccScalarFieldArithmeticsDlg.h` | SF 运算 |
| SF 从颜色 | `ccScalarFieldFromColorDlg` | `qCC/ccScalarFieldFromColorDlg.h` | 颜色→SF |
| 缩放 | `ccScaleDlg` | `qCC/ccScaleDlg.h` | 缩放工具 |
| 截面提取子对话框 | `ccSectionExtractionSubDlg` | `qCC/ccSectionExtractionSubDlg.h` | 截面参数 |
| 传感器距离 | `ccSensorComputeDistancesDlg` | `qCC/ccSensorComputeDistancesDlg.h` | 传感器距离计算 |
| 传感器散射角 | `ccSensorComputeScatteringAnglesDlg` | `qCC/ccSensorComputeScatteringAnglesDlg.h` | 散射角计算 |
| SF 作为 Vec3 | `ccSetSFAsVec3Dlg` | `qCC/ccSetSFAsVec3Dlg.h` | SF→Vec3 |
| 快捷键 | `ccShortcutDialog` | `qCC/ccShortcutDialog.h` | 快捷键管理 |
| 平滑折线 | `ccSmoothPolylineDlg` | `qCC/ccSmoothPolylineDlg.h` | 折线平滑 |
| SOR 滤波 | `ccSORFilterDlg` | `qCC/ccSORFilterDlg.h` | SOR 参数 |
| 统计检验 | `ccStatisticalTestDlg` | `qCC/ccStatisticalTestDlg.h` | 统计检验 |
| 子采样 | `ccSubsamplingDlg` | `qCC/ccSubsamplingDlg.h` | 子采样参数 |
| 展开 | `ccUnrollDlg` | `qCC/ccUnrollDlg.h` | 展开参数 |
| 体积计算 | `ccVolumeCalcTool` | `qCC/ccVolumeCalcTool.h` | 体积计算 |
| 波形对话框 | `ccWaveformDialog` | `qCC/ccWaveformDialog.h` | 波形查看 |

---

## 8. PCCM Python 映射表（当前 → 目标）

| CloudCompare C++ | PCCM 当前状态 | 目标 Python 文件 |
|---|---|---|
| `MainWindow` | ✅ 已有骨架 | `gui/main_window.py`（需增强） |
| `ccGLWindow` | ✅ 已有 offscreen blit | `gui/viewer/o3d_widget.py`（需增强） |
| `ccDBRoot` | ✅ 已有 EntityTreeModel | `gui/models/db_tree_model.py`（需增强） |
| `ccDBTree` | ✅ 已有 DBTreePanel | `gui/panels/db_tree.py`（需增强） |
| `ccPropertiesTreeDelegate` | ✅ 已有 PropertiesPanel | `gui/panels/properties.py`（需重写） |
| `ccHistogramWindow` | ✅ 已有 HistogramPanel | `gui/panels/histogram.py`（需增强） |
| `ccOverlayDialog` | ⬜ 占位 | `gui/viewer/overlay.py`（需实现） |
| `ccGraphicalSegmentationTool` | ⬜ 占位 | `gui/tools/segmentation.py`（需新建） |
| `ccGraphicalTransformationTool` | ⬜ 占位 | `gui/tools/transform.py`（需新建） |
| `ccClippingBoxTool` | ⬜ 占位 | `gui/tools/clipping.py`（需新建） |
| `ccTracePolylineTool` | ⬜ 占位 | `gui/tools/polyline.py`（需新建） |
| `ccComparisonDlg` | ⬜ 占位 | `gui/dialogs/comparison.py`（需新建） |
| `ccRegistrationDlg` | ⬜ 占位 | `gui/dialogs/registration.py`（需新建） |
| `ccPointPickingDlg` | ⬜ 占位 | `gui/tools/point_picking.py`（需新建） |
| `ccPrimitiveFactoryDlg` | ⬜ 占位 | `gui/dialogs/primitive_factory.py`（需新建） |
| `ccDisplaySettingsDlg` | ⬜ 占位 | `gui/dialogs/display_settings.py`（需新建） |
| `ccConsole` | ✅ 已有 PythonConsolePanel | `gui/panels/python_console.py` |
| 标准工具栏 | ⬜ 占位 | `gui/toolbar/standard_toolbar.py`（需新建） |
| 视图工具栏 | ⬜ 占位 | `gui/toolbar/view_toolbar.py`（需新建） |
| 渲染工具栏 | ⬜ 占位 | `gui/toolbar/render_toolbar.py`（需新建） |
| 工具工具栏 | ⬜ 占位 | `gui/toolbar/tools_toolbar.py`（需新建） |
| 状态栏 | ⬜ 占位 | `gui/status_bar.py`（需新建） |
| `ccPluginManager` | ✅ 已有 PluginManager | `plugins/__init__.py`（需增强） |

---

## 9. 核心交互流程

```
用户点击菜单/工具栏按钮
        │
        ▼
QAction.triggered() → MainWindow.doActionXxx()
        │
        ├── 需要参数 → 弹出对应 QDialog（由 ParamSpec 自动构建）
        │                  │
        │                  ▼ 用户点击 OK
        │
        ▼
ccMainAppInterface.getActiveGLWindow() → 获取当前 3D 视口
        │
        ▼
调用 CCCoreLib 算法（纯计算，不涉及 Qt）
        │
        ▼
结果 → ccHObject（新的点云/网格/标量场）
        │
        ▼
addToDB(result) → ccDBRoot.addEntity() → 刷新 DB 树 + 3D 视口
```

---

## 10. 3D 视口渲染流程

```
ccGLWindowInterface（OpenGL 渲染窗口）
        │
        ├── initializeGL() → 初始化 OpenGL 上下文
        ├── paintGL() → 渲染所有 ccDrawableObject
        ├── mousePressEvent() → 开始交互（旋转/平移/缩放）
        ├── mouseMoveEvent() → 更新交互
        ├── mouseReleaseEvent() → 结束交互
        ├── wheelEvent() → 缩放
        └── resizeGL() → 更新视口
                │
                ▼
        ccGLDrawContext → 绘制所有可见实体
                │
                ├── ccPointCloud::draw() → 绘制点
                ├── ccMesh::draw() → 绘制三角面
                ├── ccPolyline::draw() → 绘制线
                └── ccGenericPrimitive::draw() → 绘制图元
```

---

## 11. 下一步：T0 实施建议

基于以上分析，T0 需要重点做的 6 个批次：

1. **主窗口 + 菜单重构** → 对齐 `MainWindow` 的完整菜单结构（File/Edit/View/Tools/Plugins/Help）
2. **3D 视口增强** → 对齐 `ccGLWindow` 的拾取、Overlay、坐标显示
3. **DB 树增强** → 对齐 `ccDBTree` 的右键菜单、多选、拖拽
4. **属性面板重写** → 对齐 `ccPropertiesTreeDelegate` 的动态属性编辑
5. **工具栏** → 对齐 CloudCompare 的 4 个工具栏
6. **状态栏 + 进度对话框** → 对齐状态反馈体验

**关键发现**：CloudCompare 的 `qCC/` 目录有 80+ 个 C++ 文件，其中约 50 个是对话框。PCCM 可以用 `ParamSpec` 自动生成大部分对话框，大幅减少 GUI 代码量。
