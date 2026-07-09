"""Dialog package: modal parameter dialogs for algorithms.

Each dialog reads an algorithm's ``params`` tuple and dynamically
builds a form via :func:`pccm.gui.dialogs.build_param_dialog`.
"""

from pccm.gui.dialogs.build_param_dialog import build_param_dialog  # noqa: F401

__all__ = ["build_param_dialog"]
