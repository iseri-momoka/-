"""Core data model and document management.

This package provides the application's data layer — entities, commands,
history, signals — and must **never** import PySide6.

See :mod:`pccm.core.document` for the main ``Document`` class.
"""

from pccm.core.document import Document
from pccm.core.errors import (
    AlgorithmError,
    DocumentError,
    FileFormatError,
    PCCMError,
    PluginError,
    UndoError,
)
from pccm.core.history import (
    AddEntityCommand,
    Command,
    DeleteEntityCommand,
    History,
    ReplaceEntityCommand,
)
from pccm.core.signals import bus
from pccm.core.types import Entity, EntityKind, ScalarField, Unit

__all__ = [
    # document
    "Document",
    # types
    "Entity",
    "EntityKind",
    "ScalarField",
    "Unit",
    # history
    "Command",
    "AddEntityCommand",
    "DeleteEntityCommand",
    "ReplaceEntityCommand",
    "History",
    # signals
    "bus",
    # errors
    "PCCMError",
    "FileFormatError",
    "AlgorithmError",
    "PluginError",
    "DocumentError",
    "UndoError",
]
