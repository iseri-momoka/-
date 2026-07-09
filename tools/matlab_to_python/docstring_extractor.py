"""Extract H1 line and parameter list from a MATLAB ``.m`` file.

Outputs YAML for use with ``template_algorithm.py``::

    python tools/matlab_to_python/docstring_extractor.py path/to/func.m
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def parse_h1(text: str) -> str:
    """Return the first contiguous comment block after ``function``."""
    lines = text.splitlines()
    in_func = False
    block: list[str] = []
    for line in lines:
        if line.strip().startswith("function"):
            in_func = True
            continue
        if not in_func:
            continue
        stripped = line.strip()
        if stripped.startswith("%"):
            block.append(stripped.lstrip("% ").rstrip())
        elif stripped == "" and block:
            break
        elif block:
            break
    return "\n".join(block).strip()


def parse_signature(text: str) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    """Extract ``[outputs] = name(inputs)`` from the ``function`` line."""
    m = re.search(r"function\s+(.*?)\s*=\s*(\w+)\s*\((.*?)\)", text, re.DOTALL)
    if not m:
        return "", [], []
    out_block, name, in_block = m.group(1), m.group(2), m.group(3)
    outputs = [s.strip() for s in re.split(r"\s*,\s*", out_block) if s.strip()]
    inputs = [(s.strip().rstrip(","), "") for s in re.split(r"\s*,\s*", in_block) if s.strip()]
    return name, list(zip(outputs, [""] * len(outputs))), inputs


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: docstring_extractor.py <file.m> [file.m ...]", file=sys.stderr)
        return 1

    import yaml

    for path_str in sys.argv[1:]:
        path = Path(path_str)
        text = path.read_text(encoding="utf-8", errors="replace")
        name, outputs, inputs = parse_signature(text)
        h1 = parse_h1(text)
        info = {
            "source_file": str(path),
            "name": name,
            "h1": h1,
            "outputs": [o[0] for o in outputs],
            "inputs": [i[0] for i in inputs],
        }
        print(f"--- {path} ---")
        print(yaml.safe_dump(info, sort_keys=False, allow_unicode=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
