#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from logic_engine.config import load_settings  # noqa: E402
from logic_engine.engine import LogicEngine  # noqa: E402


def main() -> int:
    settings = load_settings()
    engine = LogicEngine(settings)
    engine.bootstrap_catalog()
    result = engine.run_retention_sweep()
    print(json.dumps(result.model_dump(mode="json"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
