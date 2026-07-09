"""Base protocol and data types for all point-cloud algorithms.

Every algorithm in PCCM implements the :class:`Algorithm` protocol and
declares its parameters via :class:`ParamSpec`.  The GUI reads these
declarations to auto-generate dialogs; the CLI can use them for scripting.

This module must **not** import PySide6.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import numpy as np

if TYPE_CHECKING:
    from pccm.core.document import Document

# ---------------------------------------------------------------------------
# Param types
# ---------------------------------------------------------------------------


class ParamType(enum.Enum):
    """Supported parameter types for algorithm dialogs."""

    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    STRING = "string"
    ENUM = "enum"
    VECTOR3 = "vector3"
    POINT_CLOUD_REF = "pcd_ref"
    MESH_REF = "mesh_ref"


# ---------------------------------------------------------------------------
# ParamSpec — one parameter declaration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParamSpec:
    """Declarative description of a single algorithm parameter.

    GUI code reads these to auto-generate ``QDialog`` form fields.
    Algorithm ``run()`` receives them as keyword arguments.
    """

    name: str
    label: str
    type: ParamType
    default: Any = None
    min: float | None = None
    max: float | None = None
    options: tuple[str, ...] | None = None
    help: str = ""

    def validate(self, value: Any) -> None:
        """Raise ``ValueError`` if *value* violates this spec."""
        if self.type == ParamType.FLOAT:
            if not isinstance(value, (int, float)):
                raise TypeError(f"{self.name}: expected float, got {type(value)}")
            if self.min is not None and value < self.min:
                raise ValueError(f"{self.name}={value} < min={self.min}")
            if self.max is not None and value > self.max:
                raise ValueError(f"{self.name}={value} > max={self.max}")
        elif self.type == ParamType.INT:
            if not isinstance(value, int):
                raise TypeError(f"{self.name}: expected int, got {type(value)}")
            if self.min is not None and value < self.min:
                raise ValueError(f"{self.name}={value} < min={self.min}")
            if self.max is not None and value > self.max:
                raise ValueError(f"{self.name}={value} > max={self.max}")
        elif self.type == ParamType.ENUM:
            if self.options is not None and value not in self.options:
                raise ValueError(f"{self.name}: {value!r} not in {self.options}")


# ---------------------------------------------------------------------------
# RunContext — passed to Algorithm.run()
# ---------------------------------------------------------------------------


@dataclass
class RunContext:
    """Context object passed to every algorithm invocation.

    Provides access to the document, selected entities, a progress callback,
    and a logger.  Algorithms must not hold strong references to the
    document beyond the lifetime of a single ``run()`` call.
    """

    document: "Document"
    selected_ids: list[str]
    progress: Any = None  # Callable[[float, str], None]
    logger: Any = None  # logging.Logger

    def report(self, fraction: float, message: str = "") -> None:
        """Report progress (0.0–1.0)."""
        if self.progress is not None:
            self.progress(fraction, message)


# ---------------------------------------------------------------------------
# AlgorithmResult
# ---------------------------------------------------------------------------


@dataclass
class AlgorithmResult:
    """Return value from :meth:`Algorithm.run`.

    One or more output entities, an optional scalar field, an optional
    transform, plus free-form diagnostics for logging / testing.
    """

    entities: list[Any] = field(default_factory=list)  # Entity objects
    scalar_field: Any | None = None  # ScalarField | None
    transform: np.ndarray | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    display_name: str = ""


# ---------------------------------------------------------------------------
# Algorithm protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Algorithm(Protocol):
    """Protocol that every algorithm must satisfy.

    Implementations are plain classes (no base class required).  They must
    declare the following class attributes and implement ``run()``.
    """

    id: str  # Unique identifier, e.g. "filter.voxel"
    name: str  # Human-readable name, e.g. "Voxel Downsampling"
    category: str  # Menu grouping, e.g. "Filter"
    params: tuple[ParamSpec, ...]  # Parameter declarations

    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        """Execute the algorithm.

        Parameters
        ----------
        ctx : RunContext
            Provides the document, selected entity ids, progress callback.
        **values :
            Keyword arguments matching the declared ``params``.

        Returns
        -------
        AlgorithmResult
            Output entities, scalar field, diagnostics.
        """


# ---------------------------------------------------------------------------
# AlgorithmBase — optional concrete base (not required by Protocol)
# ---------------------------------------------------------------------------


class AlgorithmBase(ABC):
    """Optional convenience base class.

    Provides default attribute stubs and a ``validate_params`` helper.
    Algorithms may use this or simply implement the Protocol directly.
    """

    id: str = ""
    name: str = ""
    category: str = ""
    params: tuple[ParamSpec, ...] = ()

    def validate_params(self, **values: Any) -> dict[str, Any]:
        """Validate *values* against ``self.params``; return resolved dict."""
        resolved: dict[str, Any] = {}
        defaults = {p.name: p.default for p in self.params}
        merged = {**defaults, **values}
        for spec in self.params:
            value = merged[spec.name]
            if value is None:
                value = spec.default
            spec.validate(value)
            resolved[spec.name] = value
        return resolved

    @abstractmethod
    def run(self, ctx: RunContext, **values: Any) -> AlgorithmResult:
        """Execute the algorithm."""
