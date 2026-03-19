#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

changed="$(git diff --name-only -- 'skills/*/SKILL.md' || true)"
if [[ -n "$changed" ]]; then
  echo "Frontmatter immutability gate failed. SKILL.md files changed:" >&2
  echo "$changed" >&2
  exit 1
fi

echo "Frontmatter immutability gate passed."
