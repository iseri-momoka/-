# MATLAB Port Workflow for PCCM Plugins

## Overview

Every MATLAB algorithm that needs to run inside PCCM goes through a standard
porting process documented here.  The goal is **numerical parity** with a
quantified tolerance, not line-by-line translation.

---

## Step 1 — Inventory

```bash
python tools/matlab_to_python/docstring_extractor.py \
    src/matlab/ground_filter.m \
    > plugins/matlab/ground_filter_csf/reference.yml
```

Produces a YAML file listing: function name, input/output parameters,
default values, and MATLAB toolbox dependencies.

## Step 2 — Scaffold

```bash
python tools/matlab_to_python/template_algorithm.py ground_filter_csf
```

Creates the plugin directory structure:

```
src/pccm/plugins/matlab/ground_filter_csf/
├── __init__.py
├── algorithm.py        ← skeleton Algorithm subclass
├── plugin.toml
├── reference.yml       ← from Step 1
tests/unit/plugins/matlab/
└── test_ground_filter_csf.py
tests/fixtures/matlab/ground_filter_csf/
├── input.npy
├── output_expected.npy
```

## Step 3 — Capture Reference Output

Run the MATLAB function in MATLAB, export the result as `.npy`:

```matlab
result = ground_filter_csf(input_points, 0.5, 500);
save('output_expected.mat', 'result');
```

Convert with `scipy.io.loadmat` → `np.save('output_expected.npy', arr)`.

## Step 4 — Port to Python

Data layout mapping (MATLAB → Python):

| MATLAB | Python/NumPy |
|---|---|
| `Nx3 double` | `np.ndarray (N,3) float64` |
| `pcdownsample` | `o3d.pcd.voxel_down_sample` |
| `pcnormals` | `o3d.pcd.estimate_normals` |
| `pcregistericp` | `o3d.pipelines.registration.registration_icp` |
| `pcfitplane` | `o3d.pcd.segment_plane` |
| `pcdenoise` | `o3d.pcd.remove_statistical_outlier` |
| `mldivide` (`\`) | `np.linalg.lstsq` (or `np.linalg.solve` for square) |
| `bsxfun` / implicit broadcast | NumPy array broadcasting |
| `zeros(m,n,'double')` | `np.zeros((m,n))` |
| `for` loops | Vectorise first; loop only if unavoidable |

## Step 5 — Unit Tests

```bash
pytest tests/unit/plugins/matlab/test_ground_filter_csf.py -v
```

- Compare output to `output_expected.npy` with `np.testing.assert_allclose(rtol=1e-5, atol=1e-6)`.
- Non-deterministic algorithms must set `np.random.seed(42)`.
- Include an **idempotency test**: same input → same output.

## Step 6 — Integration

Import the algorithm module so its `register()` fires:

```python
import pccm.plugins.matlab.ground_filter_csf.algorithm
```

Then it appears in `Plugins → MATLAB → CSF Ground Filter` and the
algorithm registry.

## Step 7 — Documentation

Add a one-liner to `docs/plugin_author_guide.md` under "MATLAB ports".

---

## Tolerance Guidelines

| Metric | Target |
|---|---|
| Coordinate error | < 1e-5 m (for metric inputs) |
| Scalar field | < 1e-5 relative |
| Index arrays | Bit-identical |
| Runtime (per 1M points) | < 2× MATLAB baseline |
