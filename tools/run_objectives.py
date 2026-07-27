#!/usr/bin/env python3
"""Run snapshot + dashboard objective builders."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent


def main() -> int:
    for script in ("compute_objectives.py", "build_objectives_dashboard.py"):
        path = TOOLS / script
        print(f"==> {script}")
        ns = runpy.run_path(str(path), run_name="__not_main__")
        code = ns["main"]()
        if code:
            return int(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
