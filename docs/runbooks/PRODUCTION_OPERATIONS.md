# LiNKskills Production Operations Runbook

## Production requirements
- GSM-only secret resolution (`LOGIC_ENGINE_SECRET_PROVIDER=gsm`).
- `LOGIC_ENGINE_ENV=production` with fail-closed behavior on secret failure.
- API auth keys provisioned in GSM and mapped to `config/api_keys.json` secret_name fields.

## Deploy
1. Copy `deploy/production/.env.example` to `deploy/production/.env`.
2. Fill non-secret values and `*_SECRET_NAME` fields only.
3. Render runtime env from GSM:
   - `deploy/production/render-env-from-gsm.sh`
4. Start services:
   - `docker compose -f deploy/production/docker-compose.yml --env-file deploy/production/.env.runtime up -d`

## Safe mode response
- Check: `GET /v1/ops/safe-mode`.
- If safe mode is active due GSM failure, restore GSM access then restart API service.
- Validate write path by running a controlled `POST /v1/runs` request.

## Retention operations
- Daily retention worker must run and be monitored.
- Validate retention windows:
  - failure diagnostics: 30 days
  - disclosure/audit: 180 days
  - financial ledger: 7 years
