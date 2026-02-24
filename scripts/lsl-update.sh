#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: $REPO_ROOT is not a git repository." >&2
  exit 1
fi

# MAS preflight: verify internalized GW gateway structure before branching.
GW_REQUIRED_FILES=(
  "tools/gw/src/cli.py"
  "tools/gw/src/requirements.txt"
)
GW_REQUIRED_DIRS=(
  "tools/gw/src/services"
  "tools/gw/src/utils"
)

for gw_file in "${GW_REQUIRED_FILES[@]}"; do
  if [[ ! -f "$gw_file" ]]; then
    echo "Error: missing required GW file '$gw_file'." >&2
    exit 1
  fi
done
for gw_dir in "${GW_REQUIRED_DIRS[@]}"; do
  if [[ ! -d "$gw_dir" ]]; then
    echo "Error: missing required GW directory '$gw_dir'." >&2
    exit 1
  fi
done

MACHINE_RAW="$(hostname)"
MACHINE="$(echo "$MACHINE_RAW" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-*//;s/-*$//')"
TS_TAIPEI="$(TZ=Asia/Taipei date +%Y%m%d-%H%M%S)"
BRANCH="dev-${MACHINE}-${TS_TAIPEI}"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
  git checkout -b "$BRANCH"
fi

git add .

if git diff --cached --quiet; then
  echo "No staged changes. Nothing to commit."
  exit 0
fi

COMMIT_MSG="$(python3 - <<'PY'
import subprocess

files = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).strip().splitlines()
shortstat = subprocess.check_output(["git", "diff", "--cached", "--shortstat"], text=True).strip()
count = len([f for f in files if f.strip()])
preview = ", ".join(files[:5]) if files else "repository updates"
if count > 5:
    preview += ", ..."
if not shortstat:
    shortstat = "content changes"
print(f"chore(sync): AI summary - updated {count} file(s) ({shortstat}) | {preview}")
PY
)"

git commit -m "$COMMIT_MSG"
git push -u origin "$BRANCH"

echo "Pushed branch: $BRANCH"
