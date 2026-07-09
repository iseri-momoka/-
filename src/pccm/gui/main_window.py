"""Application main window — the top-level QMainWindow.

Holds:
- Central 3D viewer (offscreen Open3D widget)
- DB tree dock (left)
- Properties / histogram docks (right)
- Python console dock (bottom)
- Menu and toolbar (top)

The window subscribes to :mod:`pccm.core.signals` events to keep
in sync with the Document model.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pccm.core.document import Document
from pccm.core.signals import (
    bus,
    HISTORY_CHANGED,
    SELECTION_CHANGED,
    ENTITY_ADDED,
    ENTITY_REMOVED,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDockWidget, QMainWindow as QMainWindowType

logger = logging.getLogger(__name__)


class MainWindow:
    """The top-level PCCM application window.

    Coordinates menu bar, toolbars, dock panels, and the 3D viewer.
    All public attributes below are accessed by action modules.
    """

    def __init__(self) -> None:
        from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

        self._qmain = QMainWindow()
        self._qmain.setWindowTitle("PCCM — Point Cloud Compare & Manage")
        self._qmain.resize(1400, 900)

        # Document model
        self.document = Document()

        # Mutable dicts populated during _build_layout
        self.dock_widgets: dict[str, QDockWidget] = {}
        self.actions: dict[str, object] = {}

        self._build_menu()
        self._build_layout()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> None:
        self._qmain.show()

    @property
    def qmain(self):
        """Underlying QMainWindow (for tests)."""
        return self._qmain

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        from PySide6.QtWidgets import QMenuBar

        menu_bar = self._qmain.menuBar()
        if menu_bar is None:
            return

        from pccm.gui.actions.file_actions import create_file_actions
        from pccm.gui.actions.edit_actions import create_edit_actions
        from pccm.gui.actions.view_actions import create_view_actions

        # ── File menu ────────────────────────────────────────────
        file_menu = menu_bar.addMenu("&File")
        file_acts = create_file_actions(self._qmain)
        self.actions.update(file_acts)
        for key in ("open", "open_recent", "save_project", "save_as", "export", "sep1", "exit"):
            if key in file_acts:
                file_menu.addAction(file_acts[key])

        # ── Edit menu ────────────────────────────────────────────
        edit_menu = menu_bar.addMenu("&Edit")
        edit_acts = create_edit_actions(self._qmain)
        self.actions.update(edit_acts)
        for key in ("undo", "redo", "sep1", "select_all", "deselect", "delete"):
            if key in edit_acts:
                edit_menu.addAction(edit_acts[key])

        # ── View menu ────────────────────────────────────────────
        view_menu = menu_bar.addMenu("&View")
        view_acts = create_view_actions(self._qmain)
        self.actions.update(view_acts)
        view_presets = view_menu.addMenu("Camera &Presets")
        for key in ("top", "bottom", "front", "back", "left", "right", "iso"):
            act_name = f"view_{key}"
            if act_name in view_acts:
                view_presets.addAction(view_acts[act_name])
        view_menu.addAction(view_acts.get("fit"))
        view_menu.addSeparator()
        for key in ("toggle_db_tree", "toggle_properties", "toggle_histogram", "toggle_python_console"):
            if key in view_acts:
                view_menu.addAction(view_acts[key])
        view_menu.addSeparator()
        if "fullscreen" in view_acts:
            view_menu.addAction(view_acts["fullscreen"])

        # ── Plugins menu (placeholder) ───────────────────────────
        plugins_menu = menu_bar.addMenu("&Plugins")
        _ = plugins_menu  # will be populated by PluginManager at startup

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Build the dock layout and 3D viewer."""
        from PySide6.QtWidgets import QWidget, QVBoxLayout
        from PySide6.QtCore import Qt

        # Central widget: 3D viewer
        from pccm.gui.viewer.o3d_widget import Open3DWidget
        from pccm.gui.viewer.scene import ViewerService

        central = QWidget(self._qmain)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.viewer = Open3DWidget(central)
        layout.addWidget(self.viewer)
        self._qmain.setCentralWidget(central)

        # Connect Document → Viewer via ViewerService
        self.viewer_service = ViewerService(self.document, self.viewer)

        # ── Dock panels ────────────────────────────────────────
        from pccm.gui.panels.db_tree import DBTreePanel
        from pccm.gui.panels.properties import PropertiesPanel
        from pccm.gui.panels.histogram import HistogramPanel
        from pccm.gui.panels.python_console import PythonConsolePanel

        self.db_tree_panel = DBTreePanel(self.document)
        self.properties_panel = PropertiesPanel(self.document)
        self.histogram_panel = HistogramPanel(self.document)
        self.console_panel = PythonConsolePanel(self.document)

        # Register for toggle actions and dock lookup
        self.dock_widgets = {
            "DB Tree": self.db_tree_panel.qdock,
            "Properties": self.properties_panel.qdock,
            "Histogram": self.histogram_panel.qdock,
            "Python Console": self.console_panel.qdock,
        }

        self._qmain.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.db_tree_panel.qdock)
        self._qmain.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_panel.qdock)
        self._qmain.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.histogram_panel.qdock)
        self._qmain.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_panel.qdock)

        # ── Load stylesheet ────────────────────────────────────
        self._load_stylesheet()

    def _load_stylesheet(self) -> None:
        """Load the default dark-theme QSS."""
        qss = Path(__file__).parent / "resources" / "styles" / "default.qss"
        if qss.exists():
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                app.setStyleSheet(qss.read_text(encoding="utf-8"))
                logger.debug("Loaded stylesheet: %s", qss)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        """Subscribe to Document events."""
        bus.connect(ENTITY_ADDED, lambda sender, **kw: self._on_entity_added(kw))
        bus.connect(ENTITY_REMOVED, lambda sender, **kw: self._on_entity_removed(kw))
        bus.connect(SELECTION_CHANGED, lambda sender, **kw: self._on_selection_changed(kw))
        bus.connect(HISTORY_CHANGED, lambda sender, **kw: self._on_history_changed(kw))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_entity_added(self, kw: dict) -> None:
        logger.debug("Entity added: %s", kw.get("entity_id"))

    def _on_entity_removed(self, kw: dict) -> None:
        logger.debug("Entity removed: %s", kw.get("entity_id"))

    def _on_selection_changed(self, kw: dict) -> None:
        logger.debug("Selection changed: %s", kw.get("selected_ids"))

    def _on_history_changed(self, kw: dict) -> None:
        can_undo = kw.get("can_undo", False)
        can_redo = kw.get("can_redo", False)
        logger.debug("History changed: can_undo=%s, can_redo=%s", can_undo, can_redo)
        # Keep undo/redo actions in sync
        undo_act = self.actions.get("undo")
        redo_act = self.actions.get("redo")
        if undo_act is not None:
            undo_act.setEnabled(can_undo)  # type: ignore[union-attr]
        if redo_act is not None:
            redo_act.setEnabled(can_redo)  # type: ignore[union-attr]
