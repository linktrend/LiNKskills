#!/usr/bin/env bash
set -euo pipefail

"$(dirname "$0")/../bin/pw-cli" --help >/dev/null
"$(dirname "$0")/../bin/pw-cli" --version >/dev/null
