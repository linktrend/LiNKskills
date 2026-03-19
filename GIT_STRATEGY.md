# Git Strategy (Origin Source of Truth)

## Scope
This strategy applies to the LiNKskills repository:
- Origin (authoritative): `https://github.com/linktrend/LiNKskills`

`origin` is the only writable remote in normal operation.
If an additional upstream remote is added for comparison/sync, it must be fetch-only.

## Source-of-Truth Rules
1. All new work lands in `origin` via pull requests (normal flow).
2. Production releases are built only from commits present on `origin/main`.
3. Local branches are disposable; `origin/main` is authoritative history.
4. Operational docs and control-plane contracts in this repo are authoritative over mirrored copies elsewhere.

## Remote Safety Controls
Required local remote configuration:

```bash
git remote set-url origin https://github.com/linktrend/LiNKskills.git
git config remote.pushDefault origin
git config branch.main.remote origin
git config branch.main.merge refs/heads/main
```

If you add `upstream`, hard-block pushes to it:

```bash
git remote add upstream <upstream-url>
git remote set-url --push upstream no_push
```

Verify:

```bash
git remote -v
```

Expected:
- `origin` fetch/push -> `https://github.com/linktrend/LiNKskills.git`
- `upstream` (optional) fetch -> `<upstream-url>`
- `upstream` (optional) push -> `no_push`

## Branching and PR Model
- Trunk: `main`
- Working branches: short-lived only
  - `feat/*`
  - `fix/*`
  - `docs/*`
  - `ops/*`
  - `sync/*`
- No direct trunk pushes in normal operation
- Merge policy: PR-based with approvals + required checks

## Sync Model (If External Source Is Introduced)
Use dedicated sync branches and PRs:
- branch format: `sync/<source>-YYYYMMDD-HHMM`
- merge external changes into sync branch first
- run full validation/test gates
- merge to `main` only through PR after approvals

## LiNKskills MAS Workflow (Operational)
Use repository scripts for disciplined branch/review/deploy flow:

```bash
./scripts/lsl-update.sh
python3 scripts/lsl-review.py --repo-root . --remote origin --output reports/sync-report.json
./scripts/lsl-deploy.sh
```

Operational intent:
1. `lsl-update`: commit/push current work to dev branch.
2. `lsl-review`: validate incoming branches and produce merge report.
3. `lsl-deploy`: validate + deploy from trunk.

## Required Validation Gates Before Merge
1. Global validator:

```bash
python3 validator.py --repo-root . --scan-all
```

2. Frontmatter immutability check:

```bash
bash scripts/ci-check-frontmatter.sh
```

3. Logic Engine tests (when touching `services/logic-engine`):

```bash
python3 -m unittest discover -s services/logic-engine/tests -v
```

4. Registry rebuild check (when touching catalog/compiler/policy):

```bash
python3 services/logic-engine/scripts/build_registry.py --repo-root . --output services/logic-engine/generated/catalog.json --packages services/logic-engine/config/packages.json
```

## GitHub Enforcement (Recommended)
On `main`, enforce:
1. Pull request required before merge
2. At least 2 approvals
3. Code owner review required
4. Dismiss stale approvals on new commits
5. Conversation resolution required
6. Force pushes blocked
7. Branch deletion blocked
8. Signed commits required
9. Required status checks must pass

## Release and Promotion
1. Merge validated changes to `main`.
2. Tag release from `main` (`mvo-vX.Y.Z`).
3. Deploy by commit SHA/tag for traceability.

## Daily Operating Commands
Update local trunk safely:

```bash
git fetch origin --prune
git checkout main
git pull --ff-only origin main
```

Create feature branch:

```bash
git checkout -b feat/<short-name>
```

Push branch for PR:

```bash
git push -u origin feat/<short-name>
```

## Incident Safety
If remote settings are lost, immediately re-apply:

```bash
git remote set-url origin https://github.com/linktrend/LiNKskills.git
git config remote.pushDefault origin
```

If `upstream` exists, re-apply push block:

```bash
git remote set-url --push upstream no_push
```

Then verify with `git remote -v` before any push.
