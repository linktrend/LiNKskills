#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REMOTE_URL="https://github.com/linktrend/LiNKskills-Library"
AUDIT_DIR="${HOME}/.lsl"
AUDIT_FILE="${AUDIT_DIR}/audit.jsonl"

mkdir -p "$AUDIT_DIR"

log_event() {
  local status="$1"
  local detail="$2"
  local ts
  local machine
  ts="$(TZ=Asia/Taipei date +%Y-%m-%dT%H:%M:%S%z)"
  machine="$(hostname)"
  python3 - "$AUDIT_FILE" "$ts" "$machine" "$status" "$detail" "$REPO_ROOT" "$REMOTE_URL" <<'PY'
import json
import sys
from pathlib import Path

audit_path = Path(sys.argv[1])
payload = {
    "timestamp_taipei": sys.argv[2],
    "machine": sys.argv[3],
    "status": sys.argv[4],
    "detail": sys.argv[5],
    "repo_root": sys.argv[6],
    "remote_url": sys.argv[7],
}
with audit_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
PY
}

cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  log_event "failed" "not a git repository"
  echo "Error: $REPO_ROOT is not a git repository." >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  log_event "failed" "working tree is not clean"
  echo "Error: working tree is not clean. Commit or stash changes before deploy." >&2
  exit 1
fi

git fetch origin --prune
git checkout main
git pull --ff-only origin main

python3 validator.py --repo-root . --scan-all

git push "$REMOTE_URL" main:main

log_event "success" "main validated and pushed"
echo "Deployment complete: main pushed to $REMOTE_URL"
