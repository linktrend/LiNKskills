# Source-of-Truth Release Discipline (LiNKskills)

- `origin/main` is the deployment source of truth for the skill catalog checkout.
- Deploy only from an immutable tag/SHA on `main`.
- Skill *files* in git are authoritative for instruction content; `lskills.catalog`
  is authoritative for certification_state / eval history / telemetry.
- Generated runtime artifacts under `.workdir/` are non-authoritative and must not
  be committed.
- Archived Logic Engine paths under `archive/logic-engine-2026-07-14/` are
  historical only — never deploy them.
- All production secrets remain in Google Secret Manager (GSM).
