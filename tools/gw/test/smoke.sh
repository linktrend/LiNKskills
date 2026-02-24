#!/usr/bin/env bash
set -euo pipefail

# Minimal registry-level wrapper check.
"$(dirname "$0")/../bin/gw" --help >/dev/null
"$(dirname "$0")/../bin/gw" --version >/dev/null
