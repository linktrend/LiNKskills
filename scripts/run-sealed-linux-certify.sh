#!/usr/bin/env bash
# Sealed Linux certification via local privileged Docker + bubblewrap.
# Does NOT touch stage, Supabase, VPS, cloud credentials, or live Lisa.
#
# Modes:
#   (A) release/promoting — DEFAULT for certification artifacts.
#       Requires externally supplied LINKSKILLS_EVAL_RUNNER_ISSUER_KEY (no
#       fallback; never the repository-visible local dev key) and a
#       digest-pinned LINKSKILLS_SEALED_CERT_IMAGE (name@sha256:<64 hex>).
#       Records issuer id + image digest; never logs the key. Fails closed
#       before mutation when missing/unpinned. Production later injects the
#       key process-only from GSM.
#
#   (B) local non-promoting — explicit opt-in for pipeline smoke tests.
#       May use the documented local HMAC key and a floating image tag, but
#       forces draft/eval_pending outcomes and never writes sealed release
#       evidence under evidence/phase10/sealed/.
#
# Usage (from repo root):
#   ./scripts/run-sealed-linux-certify.sh
#   ./scripts/run-sealed-linux-certify.sh --skill canary-echo
#   ./scripts/run-sealed-linux-certify.sh --local-non-promoting --skill canary-echo
#
# Requires: Docker Desktop (or equivalent) able to run --privileged Linux containers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

LOCAL_DEV_KEY="linkskills-local-eval-runner-issuer-key-not-for-production"
PREFLIGHT_ONLY="${LINKSKILLS_SEALED_CERT_PREFLIGHT_ONLY:-0}"

# Parse mode flags; remaining args go to certify-catalog.py.
CERT_ARGS=()
MODE_HINT="${LINKSKILLS_SEALED_CERT_MODE:-}"
NON_PROMOTING_FLAG=0
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --local-non-promoting|--non-promoting)
      NON_PROMOTING_FLAG=1
      MODE_HINT="local-non-promoting"
      shift
      ;;
    --release|--promoting)
      MODE_HINT="release"
      shift
      ;;
    *)
      CERT_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ "${NON_PROMOTING_FLAG}" -eq 1 ]]; then
  export LINKSKILLS_CERT_NON_PROMOTING=1
  export LINKSKILLS_SEALED_CERT_MODE=local-non-promoting
elif [[ "${LINKSKILLS_CERT_NON_PROMOTING:-}" =~ ^(1|true|yes|on)$ ]]; then
  MODE_HINT="local-non-promoting"
  export LINKSKILLS_SEALED_CERT_MODE=local-non-promoting
elif [[ -z "${MODE_HINT}" ]]; then
  MODE_HINT="release"
  export LINKSKILLS_SEALED_CERT_MODE=release
else
  export LINKSKILLS_SEALED_CERT_MODE="${MODE_HINT}"
fi

# Resolve image / key without logging secrets. Release mode has no defaults.
IMAGE="${LINKSKILLS_SEALED_CERT_IMAGE:-}"
ISSUER_KEY="${LINKSKILLS_EVAL_RUNNER_ISSUER_KEY:-}"
ISSUER_ID="${LINKSKILLS_EVAL_RUNNER_ISSUER_ID:-}"

if [[ "${MODE_HINT}" == "local-non-promoting" ]]; then
  IMAGE="${IMAGE:-python:3.12-slim}"
  ISSUER_KEY="${ISSUER_KEY:-${LOCAL_DEV_KEY}}"
  ISSUER_ID="${ISSUER_ID:-linkskills-eval-runner-local-non-promoting}"
  export LINKSKILLS_CERT_NON_PROMOTING=1
else
  ISSUER_ID="${ISSUER_ID:-linkskills-eval-runner-sealed-linux}"
fi

# Export issuer key into process env only — never as argv KEY=value (docker or
# preflight). Docker inherits via name-only --env; preflight inherits this env.
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY="${ISSUER_KEY}"

# Fail-closed Python preflight (shared with unit tests). Never prints the key.
# Issuer key is inherited from the exported process env (not argv).
set +e
PREFLIGHT_JSON="$(
  PYTHONPATH="${ROOT}:${PYTHONPATH:-}" \
  LINKSKILLS_SEALED_CERT_MODE="${MODE_HINT}" \
  LINKSKILLS_SEALED_CERT_IMAGE="${IMAGE}" \
  LINKSKILLS_EVAL_RUNNER_ISSUER_ID="${ISSUER_ID}" \
  LINKSKILLS_CERT_NON_PROMOTING="${LINKSKILLS_CERT_NON_PROMOTING:-}" \
  python3 - <<'PY'
import json
import os
from lib.skill_runtime.sealed_cert_mode import validate_sealed_cert_preflight

result = validate_sealed_cert_preflight(
    mode=os.environ.get("LINKSKILLS_SEALED_CERT_MODE"),
    issuer_key=os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"),
    image=os.environ.get("LINKSKILLS_SEALED_CERT_IMAGE"),
    issuer_id=os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_ID"),
)
payload = {
    "ok": result.ok,
    "mode": result.mode,
    "errors": list(result.errors),
    "image": result.image,
    "image_digest": result.image_digest,
    "issuer_id": result.issuer_id,
    "non_promoting": result.non_promoting,
}
print(json.dumps(payload))
raise SystemExit(0 if result.ok else 2)
PY
)"
PREFLIGHT_RC=$?
set -e
if [[ "${PREFLIGHT_RC}" -ne 0 ]]; then
  echo "Sealed cert preflight failed before mutation:" >&2
  if [[ -n "${PREFLIGHT_JSON:-}" ]]; then
    python3 -c 'import json,sys; d=json.load(sys.stdin); print("mode=", d.get("mode")); [print("-", e) for e in d.get("errors") or []]' <<<"${PREFLIGHT_JSON}" >&2
  else
    echo "- invalid mode/key/image (no preflight payload)" >&2
  fi
  exit 2
fi

# Re-parse in case local mode filled defaults.
IMAGE="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["image"])' <<<"${PREFLIGHT_JSON}")"
IMAGE_DIGEST="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("image_digest") or "")' <<<"${PREFLIGHT_JSON}")"
ISSUER_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["issuer_id"])' <<<"${PREFLIGHT_JSON}")"
NON_PROMOTING="$(python3 -c 'import json,sys; print("1" if json.load(sys.stdin)["non_promoting"] else "0")' <<<"${PREFLIGHT_JSON}")"
MODE="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["mode"])' <<<"${PREFLIGHT_JSON}")"

# Stamp catalog provenance from the host: governed *source* commit + tree hash.
# Never a self-referential tip SHA of a commit that will embed the catalog.
HOST_GIT_SHA="${LINKSKILLS_CATALOG_GIT_SHA:-$(git -C "${ROOT}" rev-parse HEAD 2>/dev/null || true)}"
if [[ -z "${LINKSKILLS_SOURCE_TREE_SHA256:-}" && -n "${HOST_GIT_SHA}" ]]; then
  LINKSKILLS_SOURCE_TREE_SHA256="$(
    PYTHONPATH="${ROOT}:${PYTHONPATH:-}" python3 - <<PY
from lib.skill_runtime.catalog_provenance import compute_source_tree_sha256
from pathlib import Path
print(compute_source_tree_sha256(Path("${ROOT}"), commit="${HOST_GIT_SHA}"))
PY
  )"
  export LINKSKILLS_SOURCE_TREE_SHA256
fi

echo "Sealed Linux certify: mode=${MODE} image=${IMAGE} root=${ROOT}"
if [[ -n "${IMAGE_DIGEST}" ]]; then
  echo "Sealed Linux certify: image_digest=sha256:${IMAGE_DIGEST}"
fi
echo "Sealed Linux certify: issuer_id=${ISSUER_ID} non_promoting=${NON_PROMOTING}"
echo "Note: --privileged is required for bwrap namespaces on Docker Desktop; still local-only."
# Never log LINKSKILLS_EVAL_RUNNER_ISSUER_KEY.

if [[ "${PREFLIGHT_ONLY}" == "1" || "${PREFLIGHT_ONLY}" == "true" ]]; then
  echo "Sealed cert preflight-only: ok (mode=${MODE})"
  exit 0
fi

# Encode CLI args so the inner container shell can reconstruct them safely.
if [[ "${#CERT_ARGS[@]}" -gt 0 ]]; then
  CERT_ARGS_B64="$(printf '%s\0' "${CERT_ARGS[@]}" | base64 | tr -d '\n')"
else
  CERT_ARGS_B64=""
fi

DOCKER_ENV=(
  --env "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"
  -e "LINKSKILLS_EVAL_RUNNER_ISSUER_ID=${ISSUER_ID}"
  -e "LINKSKILLS_CATALOG_GIT_SHA=${HOST_GIT_SHA}"
  -e "LINKSKILLS_SOURCE_TREE_SHA256=${LINKSKILLS_SOURCE_TREE_SHA256:-}"
  -e "LINKSKILLS_SEALED_CERT_MODE=${MODE}"
  -e "LINKSKILLS_SEALED_CERT_IMAGE=${IMAGE}"
  -e "LINKSKILLS_CERT_NON_PROMOTING=${NON_PROMOTING}"
  -e "CERT_ARGS_B64=${CERT_ARGS_B64}"
  -e "PYTHONPATH=packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:."
)
if [[ -n "${IMAGE_DIGEST}" ]]; then
  DOCKER_ENV+=(-e "LINKSKILLS_SEALED_CERT_IMAGE_DIGEST=${IMAGE_DIGEST}")
fi

docker run --rm --privileged \
  -v "${ROOT}:/repo" \
  -w /repo \
  "${DOCKER_ENV[@]}" \
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
    if [[ "${LINKSKILLS_CERT_NON_PROMOTING:-0}" == "1" ]]; then
      CERT_ARGS+=(--non-promoting)
    fi
    python3 scripts/certify-catalog.py "${CERT_ARGS[@]}"
  '
