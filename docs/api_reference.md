# PCCM 接口规范

> 本文档定义 PCCM 各模块之间的公开接口契约，供多人协同开发时参考。
> 所有接口变更必须同步更新本文档 + CHANGELOG.md。

---

## 1. CLI 接口（CloudCompare ↔ Python 桥）

**模块**：`src/pccm/cli/`
**入口**：`python -m pccm.cli [command]` 或 `pccm cli [command]`

### 1.1 命令列表

| 命令 | 用途 | 示例 |
|---|---|---|
| `list` | 列出所有已注册算法 | `pccm cli list --format json` |
| `info <id>` | 查看算法参数详情 | `pccm cli info filter.voxel` |
| `run <id>` | 执行算法 | `pccm cli run filter.voxel -i scan.ply -o out.ply -p '{"voxel_size":0.05}'` |
| `version` | 显示版本号 | `pccm cli version` |

### 1.2 JSON 输出格式

```json
// pccm cli list --format json
[
  {
    "id": "filter.voxel",
    "name": "Voxel Downsampling",
    "category": "Filter",
    "params": [
      {"name": "voxel_size", "type": "float", "default": 0.05}
    ]
  }
]
```

```json
// pccm cli run <id> --format json
{
  "status": "ok",
  "display_name": "Voxel Downsampling",
  "entities": [
    {"name": "scan_voxel", "kind": "CLOUD", "point_count": 50000}
  ],
  "diagnostics": {"original_count": 100000, "reduction": 0.5}
}
```

### 1.3 退出码

| 退出码 | 含义 |
|:---:|---|
| 0 | 成功 |
| 1 | 错误（算法不存在、文件找不到、参数错误等） |

---

## 2. 算法接口（Algorithm Protocol）

**模块**：`src/pccm/algorithms/base.py`
**注册表**：`src/pccm/algorithms/registry.py`

### 2.1 Algorithm 协议

```python
class Algorithm(Protocol):
    id: str              # 唯一标识，如 "filter.voxel"
    name: str            # 显示名称，如 "Voxel Downsampling"
    category: str        # 菜单分组，如 "Filter"
    params: tuple[ParamSpec, ...]  # 参数声明

    def run(self, ctx: RunContext, **values) -> AlgorithmResult: ...
```

### 2.2 ParamSpec

```python
@dataclass(frozen=True)
class ParamSpec:
    name: str            # 参数名（= kwargs key）
    label: str           # UI 显示标签
    type: ParamType      # FLOAT | INT | BOOL | STRING | ENUM | VECTOR3
    default: Any         # 默认值
    min: float | None    # 最小值
    max: float | None    # 最大值
    options: tuple[str, ...] | None  # ENUM 可选值
    help: str            # 帮助文本
```

### 2.3 RunContext

```python
@dataclass
class RunContext:
    document: Document        # 文档（含所有实体）
    selected_ids: list[str]   # 选中的实体 ID
    progress: Callable        # 进度回调 (fraction, message)
    logger: Logger            # 日志
```

### 2.4 AlgorithmResult

```python
@dataclass
class AlgorithmResult:
    entities: list[Entity]           # 输出实体
    scalar_field: ScalarField | None # 标量场
    transform: np.ndarray | None     # 4×4 变换矩阵
    diagnostics: dict[str, Any]      # 诊断信息
    display_name: str                # 显示名称
```

### 2.5 注册新算法

```python
# 方式 1：使用插件 API
from pccm.plugins.api import register, Algorithm, ParamSpec, ...

class MyAlg(Algorithm):
    id = "custom.my_alg"
    name = "My Algorithm"
    category = "Custom"
    params = (ParamSpec("threshold", "Threshold", ParamType.FLOAT, default=0.5),)

    def run(self, ctx, **values):
        # ... 算法逻辑 ...
        return AlgorithmResult(entities=[...])

register(MyAlg())
```

```python
# 方式 2：直接使用 registry
from pccm.algorithms.registry import registry
registry.register(MyAlg())
```

---

## 3. I/O 接口

**模块**：`src/pccm/io/`

### 3.1 读取

```python
from pccm.io import load_point_cloud

pcd = load_point_cloud("scan.las")  # 自动识别格式
pcd = load_point_cloud("scan.ply")
pcd = load_point_cloud("scan.pcd")
```

**支持格式**：PLY, PCD, LAS/LAZ, OBJ, E57

### 3.2 写入

```python
from pccm.io import save_point_cloud

save_point_cloud("output.ply", pcd)
save_point_cloud("output.las", pcd)
```

### 3.3 格式注册表

```python
from pccm.io.registry import registry

# 查看支持的格式
extensions = registry.supported_extensions()  # [".ply", ".pcd", ".las", ...]

# 自定义读写器
reader = registry.get_reader(".ply")
writer = registry.get_writer(".ply")
```

---

## 4. 核心数据模型

**模块**：`src/pccm/core/`

### 4.1 Entity

```python
@dataclass
class Entity:
    id: str                    # UUID hex
    name: str                  # 显示名称
    kind: EntityKind           # CLOUD | MESH | GROUP | ANNOTATION
    data: Any                  # open3d PointCloud / TriangleMesh / list[Entity]
    parent: Entity | None      # 父组
    visible: bool              # 可见性
    color: tuple[float, float, float]  # RGB [0,1]
    scalar_field: ScalarField | None    # 标量场
    transform: np.ndarray      # 4×4 仿射变换
    annotations: dict[str, Any] # 元数据
```

### 4.2 Document

```python
class Document:
    # 读取
    def get(entity_id) -> Entity | None
    @property entities -> dict[str, Entity]
    @property root_entities -> list[Entity]
    @property selection -> set[str]

    # 写入（均支持 undo/redo）
    def add_cloud(pcd, name=None) -> Entity
    def add_mesh(mesh, name=None) -> Entity
    def delete(entity_ids) -> None
    def replace(entity_id, new_data) -> None
    def set_selection(entity_ids) -> None

    # 撤销/重做
    def undo() / redo()
```

### 4.3 事件总线（blinker）

```python
from pccm.core.signals import (
    emit_entity_added,     # (entity_id, parent_id)
    emit_entity_removed,   # (entity_id, parent_id)
    emit_entity_replaced,  # (entity_id)
    emit_entity_renamed,   # (entity_id, old_name, new_name)
    emit_selection_changed,# (selected_ids: list[str])
    emit_visibility_changed,# (entity_id, visible: bool)
    emit_history_changed,  # (can_undo: bool, can_redo: bool)
)
```

---

## 5. 插件接口

**模块**：`src/pccm/plugins/`

### 5.1 插件 API（`pccm.plugins.api`）

```python
from pccm.plugins.api import (
    # 算法协议
    Algorithm, AlgorithmBase, AlgorithmResult,
    ParamSpec, ParamType, RunContext,

    # 数据类型
    ScalarField, Entity,

    # 受控 re-export
    numpy, o3d, scipy, sklearn, matplotlib,

    # 注册函数
    register, register_all,
)
```

### 5.2 MATLAB 移植插件结构

```
src/pccm/plugins/matlab/<name>/
├── __init__.py
├── algorithm.py       # Algorithm 实现
├── plugin.toml        # 插件清单
└── reference/         # MATLAB 参考输出 (.npy)
```

### 5.3 plugin.toml 格式

```toml
[plugin]
name = "algorithm_name"
version = "0.1.0"
entry = "pccm.plugins.matlab.<name>.algorithm"
author = "Author Name"
description = "Short description"
license = "GPL-3.0"
```

---

## 6. 分层约束（import-linter 强制）

| 层 | 禁止 import |
|---|---|
| `pccm.core` | PySide6, pccm.gui |
| `pccm.algorithms` | PySide6, pccm.gui, open3d.visualization |
| `pccm.io` | PySide6, pccm.gui |
| `pccm.spatial` | PySide6, pccm.gui |
| `pccm.tools` | PySide6, pccm.gui |
| `pccm.cli` | PySide6, pccm.gui |
| `pccm.plugins` | PySide6, pccm.gui, open3d.visualization |
| `pccm.plugins.matlab` | pccm.gui, pccm.core.document, pccm.core.history |

**唯一允许 import PySide6 的层**：`pccm.gui`

---

## 7. 版本与发布

- **当前版本**：`0.1.0.dev0`（在 `pyproject.toml` 中定义）
- **版本管理**：PEP 440（`MAJOR.MINOR.PATCH`）
- **发布流程**：见 `docs/architecture.md` § 8.4
- **CHANGELOG**：见 `CHANGELOG.md`
