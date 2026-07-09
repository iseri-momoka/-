"""GUI actions package — reusable QAction factories for menus and toolbars.

Each sub-module provides a ``create_*_actions`` function that returns a
dict of action-name → QAction suitable for both menu insertion and
toolbar buttons.
"""

from pccm.gui.actions.edit_actions import create_edit_actions  # noqa: F401
from pccm.gui.actions.file_actions import create_file_actions  # noqa: F401
from pccm.gui.actions.view_actions import create_view_actions  # noqa: F401

__all__ = ["create_file_actions", "create_edit_actions", "create_view_actions"]
