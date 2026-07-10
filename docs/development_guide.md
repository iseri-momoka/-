# PCCM 开发规范

> 团队协同编码标准，确保代码一致性。

---

## 1. Python 代码规范

### 1.1 格式化

- **工具**：ruff（line-length=100）
- **引号**：双引号
- **缩进**：4 空格
- **格式化命令**：
  ```bash
  ruff format src tests
  ruff check src tests --fix
  ```

### 1.2 类型注解

- `core/` 和 `algorithms/` 必须 `mypy --strict` 通过
- `gui/` 允许放宽（Qt 动态特性）
- 所有公共函数必须有类型注解
- 使用 `from __future__ import annotations` 延迟求值

```python
# ✅ 正确
def process_cloud(pcd: o3d.geometry.PointCloud, voxel_size: float) -> o3d.geometry.PointCloud:
    ...

# ❌ 错误
def process_cloud(pcd, voxel_size):
    ...
```

### 1.3 命名

| 类型 | 风格 | 示例 |
|---|---|---|
| 模块/文件 | snake_case | `voxel_filter.py` |
| 类 | PascalCase | `VoxelFilter` |
| 函数/方法 | snake_case | `downsample_points` |
| 常量 | UPPER_SNAKE | `MAX_POINTS` |
| 私有 | 前缀 `_` | `_internal_helper` |

### 1.4 日志

```python
import logging
logger = logging.getLogger(__name__)

# ✅ 使用 logging
logger.info("Loaded %d points", len(pcd.points))
logger.error("Failed to load %s: %s", path, exc)

# ❌ 禁止使用 print()
print("hello")  # 会被 ruff T201 拦截
```

---

## 2. Git 提交规范

### 2.1 分支命名

```
feature/<topic>     # 新功能
fix/<topic>         # 修复
release/<version>   # 发布
docs/<topic>        # 文档
refactor/<topic>    # 重构
```

### 2.2 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**type 类型**：

| type | 用途 |
|---|---|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `docs` | 文档变更 |
| `style` | 格式调整（不影响逻辑） |
| `refactor` | 重构（不改变外部行为） |
| `test` | 添加测试 |
| `chore` | 构建/CI/工具变更 |

**scope 范围**（可选）：

`core`, `algorithms`, `io`, `gui`, `cli`, `plugins`, `tools`, `docs`, `ci`, `build`

**示例**：

```
feat(algorithms): add voxel downsampling filter

Implements voxel-based point cloud downsampling with configurable
voxel size. Each output point is the centroid of its voxel cell.

Closes #12
```

### 2.3 Pre-commit 钩子

```bash
# 安装
pre-commit install

# 手动运行所有钩子
pre-commit run --all-files
```

自动运行：
- `ruff check --fix` + `ruff format`
- `mypy src/pccm/core src/pccm/algorithms`
- `import-linter`（分层约束）
- `check-yaml`, `check-toml`, `end-of-file-fixer`

---

## 3. 测试规范

### 3.1 目录结构

```
tests/
├── unit/
│   ├── algorithms/      # 算法单元测试
│   ├── io/              # I/O 测试
│   ├── plugins/         # 插件测试
│   └── tools/           # 工具测试
├── integration/         # 集成测试
├── gui/                 # GUI 测试（pytest-qt）
├── fixtures/            # 测试数据
└── reference/           # 算法基准数据
```

### 3.2 测试命名

```python
# 文件：test_voxel.py
# 函数：test_voxel_reduces_point_count, test_voxel_preserves_colors

def test_voxel_reduces_point_count():
    """Voxel downsampling should reduce point count."""
    pcd = create_test_cloud(10000)
    result = pcd.voxel_down_sample(voxel_size=0.1)
    assert len(result.points) < len(pcd.points)
```

### 3.3 运行测试

```bash
# 无 GUI 测试
pytest -m "not gui" -v

# GUI 测试（Linux）
xvfb-run pytest -m gui -v

# 特定模块
pytest tests/unit/algorithms/ -v

# 覆盖率
pytest --cov=pccm --cov-report=html
```

### 3.4 算法测试规范

```python
import numpy as np
import pytest

def test_icp_recovers_known_transform():
    """ICP should recover a known rigid transformation."""
    source = create_test_cloud(1000)
    T_true = create_random_transform(rotation_deg=5.0)

    target = source.transform(T_true, copy=True)

    result = icp_register(source, target)

    T_estimated = result.transform
    assert_allclose(T_estimated, T_true, rtol=1e-3, atol=1e-6)
```

---

## 4. 文档规范

### 4.1 模块文档字符串

```python
"""Voxel downsampling filter.

Downsamples a point cloud by grouping points into cubic voxels and
replacing each voxel's points with their centroid.

Example::

    from pccm.algorithms.filter.voxel import voxel_downsample
    result = voxel_downsample(pcd, voxel_size=0.05)
"""
```

### 4.2 函数文档字符串（NumPy 风格）

```python
def voxel_downsample(
    pcd: o3d.geometry.PointCloud,
    voxel_size: float,
) -> o3d.geometry.PointCloud:
    """Downsample a point cloud using voxel grid.

    Parameters
    ----------
    pcd : open3d.geometry.PointCloud
        Input point cloud.
    voxel_size : float
        Size of each voxel cube (in world units).

    Returns
    -------
    open3d.geometry.PointCloud
        Downsampled point cloud.

    Raises
    ------
    ValueError
        If voxel_size <= 0.

    Notes
    -----
    Each output point is the centroid of all input points within its voxel.
    Points with colors are averaged within each voxel.
    """
```

### 4.3 README 更新

每次新增模块或重大变更，更新：
1. `README.md` — 仓库结构、功能列表
2. `CHANGELOG.md` — Unreleased 部分添加条目
3. `docs/api_reference.md` — 接口变更

---

## 5. PR 提交检查清单

提交 PR 前，确保以下项目全部通过：

```bash
# 1. 格式化
ruff format src tests
ruff check src tests --fix

# 2. 类型检查
mypy src/pccm/core src/pccm/algorithms

# 3. 分层约束
python -m importlinter

# 4. 测试
pytest -m "not gui" -v

# 5. 更新文档
# - CHANGELOG.md 添加条目
# - 新算法更新 docs/api_reference.md
```

**PR 描述模板**：

```markdown
## 变更内容
- ...

## 变更类型
- [ ] feat: 新功能
- [ ] fix: 修复
- [ ] docs: 文档
- [ ] refactor: 重构
- [ ] test: 测试

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动 smoke test 通过

## 相关 Issue
Closes #...
```

---

## 6. 目录结构约定

### 6.1 新建算法模块

```
src/pccm/algorithms/<category>/
├── __init__.py        # 导出公开 API
├── <algorithm>.py     # 算法实现
└── tests/             # 可选：该算法的专用测试
```

### 6.2 新建插件

```
src/pccm/plugins/matlab/<name>/
├── __init__.py
├── algorithm.py       # Algorithm 实现
├── plugin.toml        # 插件清单
└── reference/         # MATLAB 参考输出
```

### 6.3 测试文件命名

- 单元测试：`test_<module>.py`
- 集成测试：`test_<feature>.py`
- GUI 测试：`test_<component>.py` + `@pytest.mark.gui`

---

## 7. 性能约束

| 指标 | 目标 | 说明 |
|---|:---:|---|
| 启动时间 | < 3s | 冷启动到窗口可交互 |
| 打开 5M 点云 | < 5s | PLY/LAS 格式 |
| 体素降采样 10M→1M | < 2s | voxel_size 合理 |
| ICP 配准（10 轮） | < 8s | P2P 模式 |
| Poisson 重建 | < 30s | depth=8 |

---

## 8. 常用命令速查

```bash
# 环境激活
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 格式化
ruff format src tests
ruff check src tests --fix

# 类型检查
mypy src/pccm/core src/pccm/algorithms

# 分层约束
python -m importlinter

# 测试
pytest -m "not gui" -v
pytest tests/unit/algorithms/ -v
pytest -m gui -v  # Linux (xvfb-run)

# CLI
python -m pccm.cli list
python -m pccm.cli run filter.voxel -i scan.ply -o out.ply

# CloudCompare 编译
cd 原软件代码/CloudCompare-master
cmake -S . -B build -DCMAKE_PREFIX_PATH='C:\Qt\6.8.0\msvc2022_64' -G 'Visual Studio 18 2026' -A x64
cmake --build build --config Release -- /m

# Git
git checkout -b feature/<topic>
git add -A && git commit -m "feat(module): description"
git push origin feature/<topic>
# 然后在 GitHub 创建 PR
```
