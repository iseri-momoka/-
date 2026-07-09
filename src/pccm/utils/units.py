"""Unit conversion helpers.

Supports meters, feet, inches, millimetres, and centimetres.
"""

from __future__ import annotations

from pccm.core.types import Unit

# Conversion factors: multiply source value by factor[target] to get target unit
_TO_M: dict[Unit, float] = {
    Unit.METERS: 1.0,
    Unit.FEET: 0.3048,
    Unit.INCHES: 0.0254,
    Unit.MILLIMETERS: 0.001,
    Unit.CENTIMETERS: 0.01,
}


def convert(value: float, from_unit: Unit, to_unit: Unit) -> float:
    """Convert *value* from *from_unit* to *to_unit*."""
    if from_unit is to_unit:
        return value
    return value * (_TO_M[from_unit] / _TO_M[to_unit])


def to_meters(value: float, unit: Unit) -> float:
    """Convert to metres."""
    return convert(value, unit, Unit.METERS)


def from_meters(value: float, unit: Unit) -> float:
    """Convert from metres."""
    return convert(value, Unit.METERS, unit)
