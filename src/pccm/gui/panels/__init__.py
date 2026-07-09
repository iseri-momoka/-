"""Panel package: dockable Qt widgets that mirror the Document model."""

from pccm.gui.panels.db_tree import DBTreePanel  # noqa: F401
from pccm.gui.panels.properties import PropertiesPanel  # noqa: F401
from pccm.gui.panels.histogram import HistogramPanel  # noqa: F401
from pccm.gui.panels.python_console import PythonConsolePanel  # noqa: F401

__all__ = ["DBTreePanel", "PropertiesPanel", "HistogramPanel", "PythonConsolePanel"]
