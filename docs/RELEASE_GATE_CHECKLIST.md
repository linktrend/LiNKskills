# Release Gate Checklist (LiNKskills)

- [ ] CI security gate green (tests + frontmatter + scans).
- [ ] GSM-only production env validated.
- [ ] No raw secrets in repo env files.
- [ ] Safe-mode drill documented.
- [ ] API auth key provisioning verified (`LINKSKILLS_API_KEY_AIOS`, `LINKSKILLS_API_KEY_AUTOWORK`).
- [ ] Retention worker schedule verified.
- [ ] Release pinned by immutable tag/SHA from main.
