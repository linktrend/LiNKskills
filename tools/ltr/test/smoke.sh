#!/usr/bin/env bash
set -euo pipefail

# ltr enforces secure-runtime checks before command dispatch.
export LSL_MASTER_KEY="${LSL_MASTER_KEY:-ltr-smoke-test-key}"

"$(dirname "$0")/../bin/ltr" --help >/dev/null
"$(dirname "$0")/../bin/ltr" --version >/dev/null
