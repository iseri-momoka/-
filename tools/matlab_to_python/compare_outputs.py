"""Compare a Python port's output against a MATLAB reference ``.npy``.

Usage::

    python tools/matlab_to_python/compare_outputs.py \
        --reference tests/fixtures/matlab/csf/output_expected.npy \
        --output /tmp/csf_output.npy
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def main() -> int:
    p = argparse.ArgumentParser(description="Compare Python output against MATLAB reference")
    p.add_argument("--reference", required=True, type=Path, help="Path to .npy reference")
    p.add_argument("--output", required=True, type=Path, help="Path to .npy Python output")
    p.add_argument("--rtol", type=float, default=1e-5)
    p.add_argument("--atol", type=float, default=1e-6)
    args = p.parse_args()

    ref = np.load(args.reference)
    out = np.load(args.output)
    if ref.shape != out.shape:
        print(f"Shape mismatch: ref {ref.shape} vs out {out.shape}", file=sys.stderr)
        return 2

    try:
        np.testing.assert_allclose(out, ref, rtol=args.rtol, atol=args.atol)
        print("OK: outputs match within tolerance.")
        return 0
    except AssertionError as exc:
        print(f"MISMATCH:\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
