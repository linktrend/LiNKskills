#!/usr/bin/env bash
set -euo pipefail
python3 ../bin/text-echo.py --version >/dev/null
python3 ../bin/text-echo.py --json hello >/dev/null
