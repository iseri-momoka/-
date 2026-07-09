"""PyInstaller hook — collect open3d resources that the default hook misses."""

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect open3d resources (shaders, data files, etc.)
datas = collect_data_files("open3d", excludes=["*.pyc"])

# Collect open3d submodules that may be loaded dynamically
hiddenimports = collect_submodules("open3d")

# open3d.visualisation (British spelling) may also exist
hiddenimports += collect_submodules("open3d.visualization")
hiddenimports += collect_submodules("open3d.io")

print(f"[hook-open3d] datas: {len(datas)} files")
print(f"[hook-open3d] hiddenimports: {len(hiddenimports)} modules")
