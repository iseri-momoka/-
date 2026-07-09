"""QThread-based progress reporter for long-running algorithms.

Usage::

    reporter = ProgressReporter(total_steps=100, parent=some_widget)
    reporter.updated.connect(my_label.setText)
    reporter.finished.connect(my_cleanup)
    reporter.start()  # runs in a worker thread

    # In the worker thread (e.g. via Algorithm.run):
    ctx.progress = reporter.set_progress  # type: ignore[assignment]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProgressReporter:
    """Lightweight, Qt-free progress tracker.

    Algorithms receive ``ctx.progress`` as a callable ``(float, str) -> None``.
    GUI code can wrap a ``ProgressReporter`` around it to get Qt signals.
    """

    total_steps: int = 100
    _current: int = field(default=0, init=False, repr=False)
    _fraction: float = field(default=0.0, init=False, repr=False)
    _message: str = field(default="", init=False, repr=False)

    def set_progress(self, fraction: float, message: str = "") -> None:
        """Update the progress fraction (0.0–1.0)."""
        self._fraction = max(0.0, min(1.0, fraction))
        self._message = message

    @property
    def fraction(self) -> float:
        return self._fraction

    @property
    def message(self) -> str:
        return self._message

    @property
    def is_complete(self) -> bool:
        return self._fraction >= 1.0

    def reset(self) -> None:
        self._fraction = 0.0
        self._message = ""
