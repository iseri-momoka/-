"""View-menu actions — camera presets, dock toggles, fullscreen.

Camera presets send the corresponding :class:`CameraPreset` to the
ViewerService; dock toggles show/hide individual QDockWidgets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow


def create_view_actions(win: "QMainWindow") -> dict[str, QAction]:
    actions: dict[str, QAction] = {}

    # ── Camera presets ─────────────────────────────────────────────
    for preset in ("top", "bottom", "front", "back", "left", "right", "iso"):
        act = QAction(f"View &{preset.title()}", win)
        act.triggered.connect(lambda _checked=False, p=preset: _on_camera(win, p))
        actions[f"view_{preset}"] = act

    # ── Fit to view ────────────────────────────────────────────────
    act = QAction("&Fit to View", win)
    act.setShortcut(QKeySequence("F"))
    act.triggered.connect(lambda: _on_fit(win))
    actions["fit"] = act

    # ── Separator ──────────────────────────────────────────────────
    sep = QAction(win)
    sep.setSeparator(True)
    actions["sep1"] = sep

    # ── Dock toggles ───────────────────────────────────────────────
    for dock_name in ("DB Tree", "Properties", "Histogram", "Python Console"):
        act = QAction(dock_name, win, checkable=True, checked=True)
        act.triggered.connect(lambda _checked, n=dock_name: _on_toggle_dock(win, n))
        actions[f"toggle_{dock_name.lower().replace(' ', '_')}"] = act

    # ── Fullscreen ─────────────────────────────────────────────────
    act = QAction("Toggle &Fullscreen", win)
    act.setShortcut(QKeySequence(Qt.Key_F11))
    act.triggered.connect(lambda: _on_toggle_fullscreen(win))
    actions["fullscreen"] = act

    return actions


def _on_camera(win: "QMainWindow", preset: str) -> None:
    """Switch the viewer camera to the given preset."""
    from pccm.gui.viewer.camera import CameraPreset
    from pccm.gui.main_window import logger as _log

    if not hasattr(win, "viewer_service"):
        return
    try:
        win.viewer_service.set_camera_preset(CameraPreset(preset))
    except Exception as exc:
        _log.error("Camera preset %s failed: %s", preset, exc)


def _on_fit(win: "QMainWindow") -> None:
    if hasattr(win, "viewer_service"):
        win.viewer_service.fit_to_view()


def _on_toggle_dock(win: "QMainWindow", dock_name: str) -> None:
    """Show / hide the named dock widget."""
    from pccm.gui.main_window import logger as _log

    target = None
    for dock in win.findChildren(type(win.findChild(type(win))).__bases__[0]) if False else []:
        pass
    # Use a name-based lookup: docks register their name in objectName
    for dock in win.findChildren(type(win)) if False else win.findChildren(type(win)) if False else []:
        pass
    # Simpler: rely on dock_widgets dict maintained by MainWindow
    dock = win.dock_widgets.get(dock_name) if hasattr(win, "dock_widgets") else None
    if dock is not None:
        dock.setVisible(not dock.isVisible())
    else:
        _log.debug("Dock %s not found", dock_name)


def _on_toggle_fullscreen(win: "QMainWindow") -> None:
    if win.isFullScreen():
        win.showNormal()
    else:
        win.showFullScreen()
