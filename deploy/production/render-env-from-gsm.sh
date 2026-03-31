#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/deploy/production/.env"
OUT_FILE="$ROOT_DIR/deploy/production/.env.runtime"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE"
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI is required"
  exit 1
fi

PROJECT_ID="${GCP_PROJECT_ID:-${GOOGLE_CLOUD_PROJECT:-}}"
if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID="$(awk -F= '/^(GCP_PROJECT_ID|GOOGLE_CLOUD_PROJECT)=/{print $2; exit}' "$ENV_FILE")"
fi
if [[ -z "$PROJECT_ID" ]]; then
  echo "Missing GCP project id"
  exit 1
fi

cp "$ENV_FILE" "$OUT_FILE"

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
  [[ "$line" != *"="* ]] && continue
  key="${line%%=*}"
  value="${line#*=}"
  if [[ "$key" == *_SECRET_NAME ]]; then
    base="${key%_SECRET_NAME}"
    resolved="$(gcloud secrets versions access latest --project "$PROJECT_ID" --secret "$value")"
    sed -i.bak "/^${base}=/d" "$OUT_FILE" || true
    rm -f "$OUT_FILE.bak"
    printf "\n%s=%s\n" "$base" "$resolved" >> "$OUT_FILE"
  fi
done < "$ENV_FILE"

chmod 600 "$OUT_FILE"
echo "Generated $OUT_FILE"
