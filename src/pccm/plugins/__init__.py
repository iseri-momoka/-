"""Plugin system — discovery, loading, and lifecycle management.

The ``PluginManager`` scans multiple directories for plugin packages,
uses ``importlib`` to load them, and lets each plugin register its
algorithms via :func:`pccm.plugins.api.register`.

Search order (first wins for same-named plugins):
  1. ``pccm.plugins.matlab.*``  — built-in MATLAB ports
  2. ``~/.config/pccm/plugins`` — user-installed plugins
  3. ``<project>/plugins/``     — project-local plugins (optional)
"""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pccm.algorithms.registry import AlgorithmRegistry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Plugin info container
# ---------------------------------------------------------------------------


@dataclass
class PluginInfo:
    """Descriptor for a discovered (possibly failed) plugin."""

    name: str
    version: str
    module: str
    entry: str
    author: str = ""
    description: str = ""
    path: Path | None = None
    error: str | None = None
    enabled: bool = True

    @property
    def healthy(self) -> bool:
        return self.error is None and self.enabled


# ---------------------------------------------------------------------------
# Plugin manager
# ---------------------------------------------------------------------------


class PluginManager:
    """Discover, load, and manage plugins.

    Parameters
    ----------
    registry : AlgorithmRegistry
        The shared algorithm registry that plugins register into.
    paths : list[Path]
        Directories to scan for ``plugin.toml`` manifests.
    """

    def __init__(self, registry: "AlgorithmRegistry", paths: list[Path] | None = None) -> None:
        self._registry = registry
        self._paths = list(paths or [])
        self._plugins: dict[str, PluginInfo] = {}
        self._loaded_modules: dict[str, object] = {}

    @property
    def plugins(self) -> list[PluginInfo]:
        return list(self._plugins.values())

    def discover(self) -> list[PluginInfo]:
        """Scan all paths for plugin.toml manifests and record them."""
        for base in self._paths:
            self._discover_dir(base)
        self._discover_entry_points()
        return self.plugins

    def _discover_dir(self, base: Path) -> None:
        """Scan a single directory for sub-directories with plugin.toml."""
        if not base.is_dir():
            return
        for child in sorted(base.iterdir()):
            toml = child / "plugin.toml"
            if not toml.exists():
                continue
            info = self._parse_toml(toml)
            if info is not None and info.name not in self._plugins:
                self._plugins[info.name] = info

    def _discover_entry_points(self) -> None:
        """Discover plugins registered via ``[project.entry-points]``."""
        try:
            eps = importlib.metadata.entry_points()
        except Exception:
            return
        group = eps.select(group="pccm.plugins") if hasattr(eps, "select") else []
        for ep in group:
            info = PluginInfo(
                name=ep.name,
                version="",
                module=ep.value,
                entry=ep.value,
                description=f"Entry-point plugin: {ep.value}",
            )
            if info.name not in self._plugins:
                self._plugins[info.name] = info

    def _parse_toml(self, path: Path) -> PluginInfo | None:
        """Minimal TOML reader — avoids requiring ``tomli`` on Python < 3.11."""
        try:
            text = path.read_text(encoding="utf-8")
            data: dict[str, str] = {}
            section = None
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1]
                    continue
                if "=" in line and section == "plugin":
                    key, _, val = line.partition("=")
                    data[key.strip()] = val.strip().strip("\"'")
            if not data.get("name"):
                return None
            return PluginInfo(
                name=data["name"],
                version=data.get("version", ""),
                module=data.get("module", ""),
                entry=data.get("entry", ""),
                author=data.get("author", ""),
                description=data.get("description", ""),
                path=path.parent,
            )
        except Exception as exc:
            logger.warning("Failed to parse %s: %s", path, exc)
            return None

    def load_all(self) -> list[PluginInfo]:
        """Discover then load every discovered plugin."""
        self.discover()
        for info in self.plugins:
            if not info.healthy or not info.enabled:
                continue
            self._load_one(info)
        return self.plugins

    def _load_one(self, info: PluginInfo) -> None:
        """Import the plugin module; catch errors so one failure can't cascade."""
        module_name = info.entry or info.module
        if not module_name:
            info.error = "No entry/module specified"
            return
        try:
            mod = importlib.import_module(module_name)
            self._loaded_modules[info.name] = mod
            logger.info("Loaded plugin: %s (%s)", info.name, module_name)
        except Exception as exc:
            info.error = f"{type(exc).__name__}: {exc}"
            logger.error("Plugin load failed: %s — %s", info.name, info.error)
            logger.debug(traceback.format_exc())

    def enable(self, name: str) -> None:
        info = self._plugins.get(name)
        if info is not None:
            info.enabled = True

    def disable(self, name: str) -> None:
        info = self._plugins.get(name)
        if info is not None:
            info.enabled = False

    def reload(self, name: str) -> None:
        """Reload a single plugin by name."""
        info = self._plugins.get(name)
        if info is None:
            return
        # Remove cached module
        module_name = info.entry or info.module
        if module_name in sys.modules:
            del sys.modules[module_name]
        info.error = None
        self._load_one(info)
