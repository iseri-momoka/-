"""File-menu actions — Open, Open Recent, Save, Save As, Export, Exit.

``create_file_actions`` is called once by :class:`MainWindow` and the
returned dict is wired into the menu bar and toolbar.  Individual
slots call back to the MainWindow via ``self`` (the parent).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow


def create_file_actions(win: "QMainWindow") -> dict[str, QAction]:
    actions: dict[str, QAction] = {}

    # ── Open ────────────────────────────────────────────────────────
    act = QAction("&Open…", win)
    act.setShortcut(QKeySequence.Open)
    act.setStatusTip("Open point cloud or mesh files")
    act.triggered.connect(lambda: _on_open(win))
    actions["open"] = act

    # ── Open Recent ────────────────────────────────────────────────
    act = QAction("Open &Recent", win)
    act.setEnabled(False)  # enabled once history is populated
    actions["open_recent"] = act

    # ── Save Project ───────────────────────────────────────────────
    act = QAction("&Save Project", win)
    act.setShortcut(QKeySequence.Save)
    act.setStatusTip("Save current project (.pccm)")
    act.triggered.connect(lambda: _on_save_project(win))
    actions["save_project"] = act

    # ── Save As ────────────────────────────────────────────────────
    act = QAction("Save &As…", win)
    act.setShortcut(QKeySequence("Ctrl+Shift+S"))
    act.triggered.connect(lambda: _on_save_project(win, ask_path=True))
    actions["save_as"] = act

    # ── Export Selected ────────────────────────────────────────────
    act = QAction("&Export Selected…", win)
    act.setStatusTip("Export the selected entities to a file")
    act.triggered.connect(lambda: _on_export(win))
    actions["export"] = act

    # ── Separator ──────────────────────────────────────────────────
    sep = QAction(win)
    sep.setSeparator(True)
    actions["sep1"] = sep

    # ── Exit ───────────────────────────────────────────────────────
    act = QAction("E&xit", win)
    act.setShortcut(QKeySequence.Quit)
    act.triggered.connect(win.close)
    actions["exit"] = act

    return actions


# ── slot implementations ────────────────────────────────────────────

def _on_open(win: "QMainWindow") -> None:
    """Open file dialog, then load selected files into the Document."""
    from PySide6.QtWidgets import QFileDialog

    exts = "*.ply *.las *.laz *.pcd *.e57 *.obj"
    paths, _ = QFileDialog.getOpenFileNames(
        win,
        "Open Point Cloud / Mesh",
        "",
        f"All supported ({exts});;PLY (*.ply);;LAS/LAZ (*.las *.laz);;"
        "PCD (*.pcd);;E57 (*.e57);;OBJ (*.obj);;All files (*)",
    )
    if not paths:
        return
    # Import lazily to avoid circular imports at module load time
    from pccm.io import load_point_cloud
    from pccm.gui.main_window import logger as _log

    for p in paths:
        try:
            entities = load_point_cloud(p)
            for ent in entities:
                win.document.add_entity(ent)
            _log.info("Loaded %s (%d entities)", p, len(entities))
        except Exception as exc:
            _log.error("Failed to load %s: %s", p, exc)


def _on_save_project(win: "QMainWindow", ask_path: bool = False) -> None:
    """Save / Save-As the current project."""
    # TODO: implement project serialization
    pass


def _on_export(win: "QMainWindow") -> None:
    """Export selected entities to disk."""
    from PySide6.QtWidgets import QFileDialog

    if not win.document.selection:
        return
    exts = "*.ply *.las *.pcd"
    path, _ = QFileDialog.getSaveFileName(
        win,
        "Export",
        "",
        "PLY (*.ply);;LAS (*.las);;PCD (*.pcd)",
    )
    if not path:
        return
    from pccm.io.writers import save
    from pccm.gui.main_window import logger as _log

    for eid in win.document.selection:
        ent = win.document.entities.get(eid)
        if ent is not None and ent.kind.value in ("cloud", "mesh"):
            try:
                save(ent.data, path)
                _log.info("Exported %s → %s", ent.name, path)
            except Exception as exc:
                _log.error("Export failed: %s", exc)
