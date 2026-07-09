"""Edit-menu actions — Undo, Redo, Select All, Delete.

Slots communicate with the :class:`Document` through the undo-history
command pattern and signal bus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QKeySequence

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow


def create_edit_actions(win: "QMainWindow") -> dict[str, QAction]:
    actions: dict[str, QAction] = {}

    # ── Undo ────────────────────────────────────────────────────────
    act = QAction("&Undo", win)
    act.setShortcut(QKeySequence.Undo)
    act.setStatusTip("Undo the last action")
    act.setEnabled(False)
    act.triggered.connect(lambda: _on_undo(win))
    actions["undo"] = act

    # ── Redo ────────────────────────────────────────────────────────
    act = QAction("&Redo", win)
    act.setShortcut(QKeySequence.Redo)
    act.setStatusTip("Redo the last undone action")
    act.setEnabled(False)
    act.triggered.connect(lambda: _on_redo(win))
    actions["redo"] = act

    # ── Separator ──────────────────────────────────────────────────
    sep = QAction(win)
    sep.setSeparator(True)
    actions["sep1"] = sep

    # ── Select All ─────────────────────────────────────────────────
    act = QAction("Select &All", win)
    act.setShortcut(QKeySequence.SelectAll)
    act.triggered.connect(lambda: _on_select_all(win))
    actions["select_all"] = act

    # ── Deselect ───────────────────────────────────────────────────
    act = QAction("&Deselect", win)
    act.setShortcut(QKeySequence("Escape"))
    act.triggered.connect(lambda: _on_deselect(win))
    actions["deselect"] = act

    # ── Delete Selected ────────────────────────────────────────────
    act = QAction("&Delete Selected", win)
    act.setShortcut(QKeySequence("Delete"))
    act.setStatusTip("Delete the currently selected entities")
    act.triggered.connect(lambda: _on_delete(win))
    actions["delete"] = act

    return actions


# ── slot implementations ────────────────────────────────────────────


def _on_undo(win: "QMainWindow") -> None:
    try:
        win.document.undo()
    except Exception as exc:
        logger.debug("Undo failed: %s", exc)


def _on_redo(win: "QMainWindow") -> None:
    try:
        win.document.redo()
    except Exception as exc:
        logger.debug("Redo failed: %s", exc)


def _on_select_all(win: "QMainWindow") -> None:
    all_ids = set(win.document.entities.keys())
    win.document.set_selection(all_ids)


def _on_deselect(win: "QMainWindow") -> None:
    win.document.set_selection(set())


def _on_delete(win: "QMainWindow") -> None:
    if win.document.selection:
        win.document.delete(list(win.document.selection))


import logging

logger = logging.getLogger(__name__)
