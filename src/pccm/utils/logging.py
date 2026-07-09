"""Centralized logging configuration.

Sets up a default logger with a friendly console formatter, optionally
adds a rotating file handler under the user's data directory.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DEFAULT_DATEFMT = "%H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
    quiet: bool = False,
) -> logging.Logger:
    """Configure the root logger.

    Parameters
    ----------
    level : int
        Logging level (e.g., ``logging.DEBUG``).
    log_file : Path, optional
        If given, log records are also written to this file (with
        automatic rotation at 5 MB, 3 backups).
    quiet : bool
        If True, suppress the console handler.
    """
    root = logging.getLogger()
    root.setLevel(level)
    # Remove existing handlers (idempotent)
    for h in list(root.handlers):
        root.removeHandler(h)
    fmt = logging.Formatter(_DEFAULT_FORMAT, datefmt=_DEFAULT_DATEFMT)
    if not quiet:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(level)
        ch.setFormatter(fmt)
        root.addHandler(ch)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        )
        fh.setLevel(level)
        fh.setFormatter(fmt)
        root.addHandler(fh)
    # Silence noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return root
