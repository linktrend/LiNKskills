# Source-of-Truth Release Discipline (LiNKskills)

- `origin/main` is the deployment source of truth.
- Deploy only from immutable tag/SHA on main.
- Generated runtime artifacts (for example `services/logic-engine/runtime/*`) are non-authoritative and must not be committed.
- All production secrets remain in GSM.
