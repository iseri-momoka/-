"""Custom exception hierarchy for PCCM.

Catch these in GUI code; let them propagate out of algorithms unchanged.
"""

from __future__ import annotations


class PCCMError(Exception):
    """Base exception for all PCCM errors."""


class FileFormatError(PCCMError):
    """Raised when an I/O operation encounters an unsupported or corrupt file."""


class AlgorithmError(PCCMError):
    """Raised when an algorithm fails (e.g., no convergence, bad input)."""


class PluginError(PCCMError):
    """Raised when a plugin fails to load or register."""


class DocumentError(PCCMError):
    """Raised for invalid document operations (e.g., duplicate ID)."""


class UndoError(PCCMError):
    """Raised when undo/redo is not possible (e.g., empty history stack)."""
