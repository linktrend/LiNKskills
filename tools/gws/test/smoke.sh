#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT_DIR/bin/gws" --version >/dev/null
"$ROOT_DIR/bin/gws" --help >/dev/null
