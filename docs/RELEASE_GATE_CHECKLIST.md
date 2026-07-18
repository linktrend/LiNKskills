# Release Gate Checklist (LiNKskills)

Last updated: 2026-07-18

- [ ] CI green on the release SHA (`validator.py --scan-all`, eval-suite gate, catalog index `--check`, skill_runtime unit tests).
- [ ] No Logic Engine / retired API deploy paths referenced in runbooks or compose files.
- [ ] GSM-only secret resolution for any host that flushes telemetry or runs the Librarian (no raw secrets in git).
- [ ] `lskills.catalog` seeded on the target Supabase project (`count(*)` matches skill folders).
- [ ] Consumer load path documented and verified (`docs/CONSUMER-SKILL-LOAD-PATH.md`).
- [ ] Release pinned by immutable tag/SHA from `main` (never deploy floating `latest`).
- [ ] Librarian first pass on stage uses `LIBRARIAN_DRY_RUN=true` before write-enabled runs.
