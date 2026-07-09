"""Generic parameter dialog — builds a QDialog from a list of :class:`ParamSpec`.

Given an algorithm's ``params`` tuple, this produces a form with the right
widget for each :class:`ParamType` and exposes the collected values via
:meth:`ParamDialog.values`.  All algorithm dialogs in pccm are produced
by this single builder so that adding a new algorithm does not require
writing UI code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pccm.algorithms.base import ParamSpec, ParamType


@dataclass
class _Widget:
    """Holds the editor widget and a ``get`` callable that returns its value."""

    spec: ParamSpec
    label: QLabel
    editor: QWidget
    get: callable  # type: ignore[type-arg]

    def value(self) -> Any:
        return self.get()


def _make_float(spec: ParamSpec) -> _Widget:
    sb = QDoubleSpinBox()
    sb.setDecimals(6)
    if spec.min is not None:
        sb.setMinimum(float(spec.min))
    if spec.max is not None:
        sb.setMaximum(float(spec.max))
    sb.setValue(float(spec.default))
    return _Widget(spec, QLabel(spec.label), sb, lambda: sb.value())


def _make_int(spec: ParamSpec) -> _Widget:
    sb = QSpinBox()
    if spec.min is not None:
        sb.setMinimum(int(spec.min))
    if spec.max is not None:
        sb.setMaximum(int(spec.max))
    sb.setValue(int(spec.default))
    return _Widget(spec, QLabel(spec.label), sb, lambda: sb.value())


def _make_bool(spec: ParamSpec) -> _Widget:
    cb = QCheckBox()
    cb.setChecked(bool(spec.default))
    return _Widget(spec, QLabel(spec.label), cb, lambda: cb.isChecked())


def _make_enum(spec: ParamSpec) -> _Widget:
    combo = QComboBox()
    options = spec.options or ()
    for opt in options:
        combo.addItem(str(opt))
    default = str(spec.default)
    idx = combo.findText(default)
    if idx >= 0:
        combo.setCurrentIndex(idx)
    return _Widget(spec, QLabel(spec.label), combo, lambda: combo.currentText())


def _make_vector3(spec: ParamSpec) -> _Widget:
    """Three side-by-side spin boxes: x, y, z.  Default is a 3-tuple."""
    container = QWidget()
    from PySide6.QtWidgets import QHBoxLayout

    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    default = spec.default if isinstance(spec.default, (list, tuple)) else (0.0, 0.0, 0.0)
    boxes: list[QDoubleSpinBox] = []
    for i in range(3):
        b = QDoubleSpinBox()
        b.setDecimals(6)
        b.setRange(-1e9, 1e9)
        b.setValue(float(default[i]) if i < len(default) else 0.0)
        layout.addWidget(b)
        boxes.append(b)
    return _Widget(
        spec,
        QLabel(spec.label),
        container,
        lambda: (boxes[0].value(), boxes[1].value(), boxes[2].value()),
    )


def _make_text(spec: ParamSpec) -> _Widget:
    edit = QLineEdit()
    edit.setText(str(spec.default))
    return _Widget(spec, QLabel(spec.label), edit, lambda: edit.text())


def _make_ref(spec: ParamSpec) -> _Widget:
    """Point-cloud / mesh reference — combo box of compatible entity ids.

    Populated externally by :func:`build_param_dialog` once the document
    is known.  A free-text fallback lets advanced users paste raw ids.
    """
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItem(str(spec.default), str(spec.default))
    return _Widget(
        spec,
        QLabel(spec.label),
        combo,
        lambda: combo.currentText(),
    )


_FACTORIES: dict[ParamType, callable] = {  # type: ignore[type-arg]
    ParamType.FLOAT: _make_float,
    ParamType.INT: _make_int,
    ParamType.BOOL: _make_bool,
    ParamType.ENUM: _make_enum,
    ParamType.VECTOR3: _make_vector3,
    ParamType.STRING: _make_text,
    ParamType.POINT_CLOUD_REF: _make_ref,
    ParamType.MESH_REF: _make_ref,
}


class ParamDialog(QDialog):
    """Modal dialog hosting a dynamic form of parameter widgets."""

    def __init__(
        self,
        title: str,
        params: Iterable[ParamSpec],
        ref_options: Mapping[str, list[str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(360)

        self._widgets: list[_Widget] = []
        self._ref_options = ref_options or {}

        body = QVBoxLayout(self)
        self._form = QFormLayout()
        body.addLayout(self._form)

        for spec in params:
            self._add_param(spec)

        # Help text footer
        body.addStretch(1)
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        body.addWidget(self._buttons)

    def _add_param(self, spec: ParamSpec) -> None:
        factory = _FACTORIES.get(spec.type)
        if factory is None:
            # Unknown type — fall back to text input so the user is never stuck.
            factory = _make_text
        w = factory(spec)
        self._widgets.append(w)
        # Wire up reference options if applicable
        if spec.type in (ParamType.POINT_CLOUD_REF, ParamType.MESH_REF):
            options = self._ref_options.get(spec.name, ())
            if options and isinstance(w.editor, QComboBox):
                w.editor.addItems(options)
        self._form.addRow(w.label, w.editor)
        if spec.help:
            help_lbl = QLabel(spec.help)
            help_lbl.setWordWrap(True)
            help_lbl.setStyleSheet("color: gray; font-size: 10px;")
            self._form.addRow("", help_lbl)

    def values(self) -> dict[str, Any]:
        return {w.spec.name: w.value() for w in self._widgets}


def build_param_dialog(
    title: str,
    params: Iterable[ParamSpec],
    ref_options: Mapping[str, list[str]] | None = None,
    parent: QWidget | None = None,
) -> ParamDialog:
    """Convenience constructor — used by the menu/action layer."""
    return ParamDialog(title, tuple(params), ref_options=ref_options, parent=parent)
