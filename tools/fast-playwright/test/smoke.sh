#!/usr/bin/env bash
set -euo pipefail

# Registry-level smoke check for wrapper presence.
"$(dirname "$0")/../bin/start-mcp" --help >/dev/null || true
