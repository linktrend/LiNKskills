#!/usr/bin/env python3
from __future__ import annotations

import sys
import os
from pathlib import Path

import uvicorn

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def main() -> int:
    host = os.getenv("LOGIC_ENGINE_HOST", "0.0.0.0")
    port = int(os.getenv("LOGIC_ENGINE_PORT", "8080"))
    uvicorn.run("logic_engine.main:app", host=host, port=port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
