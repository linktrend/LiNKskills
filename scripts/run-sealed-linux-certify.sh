#!/usr/bin/env bash
# Sealed Linux certification via local privileged Docker + bubblewrap.
# Does NOT touch stage, Supabase, VPS, cloud credentials, or live Lisa.
#
# Usage (from repo root):
#   ./scripts/run-sealed-linux-certify.sh
#   ./scripts/run-sealed-linux-certify.sh --skill canary-echo
#
# Requires: Docker Desktop (or equivalent) able to run --privileged Linux containers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${LINKSKILLS_SEALED_CERT_IMAGE:-python:3.12-slim}"
ISSUER_KEY="${LINKSKILLS_EVAL_RUNNER_ISSUER_KEY:-linkskills-local-eval-runner-issuer-key-not-for-production}"
ISSUER_ID="${LINKSKILLS_EVAL_RUNNER_ISSUER_ID:-linkskills-eval-runner-sealed-linux}"

# Encode CLI args so the inner container shell can reconstruct them safely.
if [[ "$#" -gt 0 ]]; then
  CERT_ARGS_B64="$(printf '%s\0' "$@" | base64 | tr -d '\n')"
else
  CERT_ARGS_B64=""
fi

echo "Sealed Linux certify: image=${IMAGE} root=${ROOT}"
echo "Note: --privileged is required for bwrap namespaces on Docker Desktop; still local-only."

docker run --rm --privileged \
  -v "${ROOT}:/repo" \
  -w /repo \
  -e "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=${ISSUER_KEY}" \
  -e "LINKSKILLS_EVAL_RUNNER_ISSUER_ID=${ISSUER_ID}" \
  -e "CERT_ARGS_B64=${CERT_ARGS_B64}" \
  -e "PYTHONPATH=packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:." \
  "${IMAGE}" \
  bash -lc '
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq bubblewrap >/dev/null
    python3 -m pip install -q PyYAML
    # Fail closed: do not set allow_unproven.
    unset LINKSKILLS_EXECUTOR_NETWORK_ISOLATION || true
    python3 - <<'"'"'PY'"'"'
from linkskills_tool_runtime.confined_exec import run_confined
import tempfile, sys
with tempfile.TemporaryDirectory() as tmp:
    r = run_confined([sys.executable, "-c", "print(\"probe-ok\")"], workspace=tmp, timeout_seconds=10)
print("isolation_probe", r.network_isolation)
if r.network_isolation != "denied":
    raise SystemExit("sealed host probe failed: expected network_isolation=denied")
PY
    CERT_ARGS=()
    if [[ -n "${CERT_ARGS_B64:-}" ]]; then
      while IFS= read -r -d "" arg; do
        CERT_ARGS+=("$arg")
      done < <(printf "%s" "$CERT_ARGS_B64" | base64 -d)
    fi
    python3 scripts/certify-catalog.py "${CERT_ARGS[@]}"
  '
