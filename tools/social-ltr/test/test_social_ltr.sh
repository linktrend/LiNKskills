#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT_DIR/bin/social-ltr" --version >/dev/null
"$ROOT_DIR/bin/social-ltr" fetch-comments --provider youtube --target-id dummy --json >/dev/null || true

echo "social-ltr smoke test complete"
