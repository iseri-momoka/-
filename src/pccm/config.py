"""Application configuration paths and user settings.

All filesystem paths used by PCCM are derived through this module so the
rest of the codebase never has to reason about platform conventions.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

# Project-wide constants ----------------------------------------------------

_APP_NAME: Final = "PCCM"
_APP_AUTHOR: Final = "PCCM"


class Config:
    """Static accessors for filesystem locations.

    The class is intentionally stateless — values are derived from
    environment variables with sensible fallbacks.
    """

    # ---- User data ------------------------------------------------------

    @staticmethod
    def user_data_dir() -> Path:
        """Per-user writable directory (settings, logs, cache)."""
        override = os.environ.get("PCCM_USER_DATA_DIR")
        if override:
            return Path(override).expanduser()
        return Path.home() / f".{_APP_NAME.lower()}"

    @staticmethod
    def user_plugin_dir() -> Path:
        """User-level plugin directory (drop-in .py packages)."""
        return Config.user_data_dir() / "plugins"

    @staticmethod
    def user_cache_dir() -> Path:
        """Cache directory (screenshot blobs, offscreen FBO)."""
        return Config.user_data_dir() / "cache"

    # ---- Application data ----------------------------------------------

    @staticmethod
    def app_plugin_dir() -> Path:
        """Built-in plugin directory bundled with the package."""
        from pccm.plugins import user_plugins as _fallback  # noqa: F401

        # The shipped plugins live alongside the package.
        from pccm import plugins as plugins_pkg

        return Path(plugins_pkg.__file__).resolve().parent

    @staticmethod
    def project_root() -> Path:
        """Path to the repository root, resolved at import time."""
        # <src/pccm/config.py> -> <repo root>
        return Path(__file__).resolve().parents[2]

    # ---- Bootstrap ------------------------------------------------------

    @staticmethod
    def ensure_directories() -> None:
        """Create writable directories that may not exist yet."""
        for path in (
            Config.user_data_dir(),
            Config.user_plugin_dir(),
            Config.user_cache_dir(),
        ):
            path.mkdir(parents=True, exist_ok=True)
