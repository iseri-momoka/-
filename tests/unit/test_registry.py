"""Tests for AlgorithmRegistry."""

from __future__ import annotations

import pytest

from pccm.algorithms.base import (
    AlgorithmBase,
    AlgorithmResult,
    ParamSpec,
    ParamType,
    RunContext,
)
from pccm.algorithms.registry import AlgorithmRegistry, registry as global_registry


class _DummyAlgorithm(AlgorithmBase):
    id = "test.dummy"
    name = "Dummy"
    category = "Test"
    params = ()

    def run(self, ctx: RunContext, **values) -> AlgorithmResult:
        return AlgorithmResult(entities=[], scalar_field=None, transform=None, diagnostics={}, display_name="dummy")


class TestRegistry:
    def test_register_and_get(self):
        reg = AlgorithmRegistry()
        alg = _DummyAlgorithm()
        reg.register(alg)
        assert reg.get("test.dummy") is alg

    def test_get_unknown_raises(self):
        reg = AlgorithmRegistry()
        with pytest.raises(KeyError):
            reg.get("nope")

    def test_by_category(self):
        reg = AlgorithmRegistry()
        reg.register(_DummyAlgorithm())
        grouped = reg.by_category()
        assert "Test" in grouped
        assert any(a.id == "test.dummy" for a in grouped["Test"])

    def test_unregister(self):
        reg = AlgorithmRegistry()
        alg = _DummyAlgorithm()
        reg.register(alg)
        reg.unregister("test.dummy")
        with pytest.raises(KeyError):
            reg.get("test.dummy")

    def test_global_registry_contains_builtins(self):
        # The default registry should have at least one filter algorithm
        # (populated by importing pccm.algorithms in pccm.algorithms.__init__).
        from pccm.algorithms.filter.voxel import VoxelDownsample
        try:
            global_registry.get(VoxelDownsample.id)
        except KeyError:
            pytest.fail("VoxelDownsample not registered in global registry")
