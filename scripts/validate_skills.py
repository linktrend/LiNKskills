#!/usr/bin/env python3
"""Canonical CLI entrypoint for skill/tool structural validation.

Delegates to repository-root ``validator.py`` — do not duplicate validation
logic in skill-local scripts.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "validator.py"
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
