# Governed execution route and start gate

**Verified:** 2026-09-10 (Asia/Taipei)

**Decision:** `AUTHENTICATED_ROUTE_READY / CURRENT_TASK_QUEUE_HOLD / NO_JOB_LAUNCHED`

This record separates a verified coordinator-side execution route from
permission to execute. It authorizes neither a Cursor run nor product work.

## Operative dispatcher

The currently working route is the dependency-free Python REST dispatcher at:

`/Users/linktrend/Documents/Codex/2026-09-09/files-pasted-by-the-user-i/outputs/cursor-cloud/cursor_cloud.py`

Its adjacent operating guide is `README.md`. These coordinator-side files are
not worker inputs and do not replace repository governance. Their pinned
SHA-256 digests are:

- dispatcher: `0cf61dc9b2f6b7f6c6b34ddf94a7c751229e9838d50ed9c1b468f5327e39e2e8`
- guide: `7626c9bacbeaa9b62d1912da2e0c1bdaf3cdd6a3179164aacb8dd70bb405f1e0`

The dispatcher uses only the Python standard library, so it has no separately
installed SDK version. It reads the existing macOS Keychain item identified by
service `Cursor-Codex-001` and account `cursor-001@linktrend.one`; the credential
value remains in Keychain/process memory and is never placed in a packet,
receipt, repository, or worker prompt.

LiNKskills also contains the installed IDE Development
`cursor-cloud-dispatch-v2` SDK interface at
`.ide-development/execution/cursor_cloud_dispatch.py`, config, and contract.
Those files are byte-identical to canonical IDE Development commit
`a78c63762bca53c17b283ca70c4f65e0de232e4b`, tree
`20f99eb03a4d0f7bef4a74627db694c063041213`, but `cursor-sdk` is not installed
in the active Python runtime. That SDK adapter is therefore a reviewed future
interface, not the operative route and not a start blocker.

## Read-only authenticated verification

On 2026-09-10 the operative client performed exactly three safe reads:
`GET /v1/me`, `GET /v1/models`, and `GET /v1/repositories`. It proved:

- authenticated account `cursor-001@linktrend.one` and a named API key;
- model `grok-4.6` admits `effort=medium` and `fast=false`;
- `https://github.com/linktrend/LiNKskills` is visible to that account; and
- 98 repositories were returned by the connected repository catalogue.

No `POST`, agent creation, provider job, paid model use, receipt write, secret
readout, or credential change occurred. The repository endpoint is strictly
rate-limited, so its result is refreshed once immediately before a real
dispatch rather than repeatedly polled.

The global queue is currently suspended except for the exact owners and
repositories in `queue-control/RESUME-SCOPE.json`. `linktrend/LiNKskills` is
listed for two other Server 01 owners, but this planning task is not an admitted
owner. The dispatcher therefore blocks a packet owned by this task before any
Cursor request. No owner may be borrowed or invented. A governed handoff or an
updated founder-authorised resume scope is required before ED-01 can dispatch.

The transport suite produced 7 PASS and 3 tests stopped early at this live
suspension guard. Those three expected to exercise uncertain-create and capacity
logic with fixture owner `test`; the guard rejected that owner first. This does
not prove a transport defect, but full 10/10 runtime acceptance remains part of
the pre-dispatch receipt. The guard was not bypassed or changed.

## Current owner and overlap inventory

- Deployment task owner: `01a089cb-ee73-7c52-9e62-4f9654114eba`.
- Repository: `linktrend/LiNKskills`.
- Planning issue/branch: issue `#323`,
  `issue/323-plan-linkskills-end-to-end-deployment-on-linkser`.
- Protected implementation baseline: `development`
  `7a813f529f7b25a40fd3e88f74fb0e86c7c728d5`, tree
  `d0bb392351994810173f730c47b63112c31e391b`.
- Planning baseline: the final pushed issue-323 commit/tree recorded in the
  planning handoff; it is not an implementation baseline.
- Bounded GitHub/worktree inspection found no open LiNKskills PR, no other
  issue-323 branch, and no dirty work outside this planning branch. The primary
  `development` checkout and detached app checkout were clean.
- Provider readback found the sole recorded LiNKskills cloud qualification job
  `LINKSKILLS-CLOUD-ENV-001` terminal `FINISHED` with agent now `IDLE`. It is
  historical environment evidence, not an active writer or reusable ownership.
- Platform task `01a0843c-0df9-74e2-907a-05c5f736d6ed` retains all active
  Server 01 repair, shared migration, identity, and runtime ownership. This plan
  neither takes it over nor dispatches a competing writer.

The inventory is refreshed immediately before admission. A newly active
LiNKskills writer, changed branch, or overlapping owned path stops dispatch and
is reconciled by its current owner.

## Narrow owner transition after approval

This is the first coordinator mutation after founder `APPROVE`, and it occurs
before a Cursor writer is created. Under an exclusive coordinator lock, read
and hash these current files:

- `/Users/linktrend/Documents/Codex/2026-09-09/files-pasted-by-the-user-i/outputs/queue-control/SUSPENDED`
- `/Users/linktrend/Documents/Codex/2026-09-09/files-pasted-by-the-user-i/outputs/queue-control/RESUME-SCOPE.json`
- `/Users/linktrend/Documents/Codex/2026-09-09/files-pasted-by-the-user-i/outputs/queue-control/agents.json`
- the matching `cursor-cloud/state/*.json` receipts.

Reconcile relevant saved agents with actual provider GET readback. Only if no
LiNKskills writer is active, atomically add this single mapping while preserving
every existing owner, repository, suspension, and limit:

```json
"01a089cb-ee73-7c52-9e62-4f9654114eba": ["linktrend/LiNKskills"]
```

Write a same-directory temporary file, validate JSON and the exact owner/repo
pair, `fsync`, rename, read back, and record before/after SHA-256 plus the
founder-approval reference. Keep `SUSPENDED`; do not broaden another owner,
impersonate an old ID, or change the ceilings of 20 outstanding jobs, 16
writers, and one live cloud writer per repository.

Rollback restores the exact prior bytes only after provider readback proves no
task-owned agent is active, then re-hashes/read-backs the file. If an enforced
policy refuses this exact approved mapping, XP-00 returns that specific failure
to the founder; it does not delete `SUSPENDED`, bypass the dispatcher, or create
another route.

## Exact admitted packet and request

Every Grok packet and every input the worker needs must first exist in GitHub at
the packet's exact accessible repository, issue branch, commit, tree, and path.
Mac-only planning files, conversation history, and prompt-only requirements are
not source inputs. The local dispatcher and Keychain item remain
coordinator-side.

The operative dispatcher binds one repository per request. Platform or consumer
implementation is never assumed to be attached. A cross-repository dependency
must be an immutable, non-secret, versioned contract/artifact already published
at an accessible GitHub revision and referenced from the LiNKskills packet, or
it remains with its owning task. LiNKskills does not copy another repository's
implementation to make it visible.

The packet supplies a stable packet ID, owner, role, repository, `issue/*` ref,
40-character commit and tree, prompt, allowed paths, acceptance commands, and
admission evidence. Before dispatch, `gh api` must prove the branch resolves to
that exact commit/tree. The REST request then admits only:

```json
{
  "model": {
    "id": "grok-4.6",
    "params": [
      {"id": "effort", "value": "medium"},
      {"id": "fast", "value": "false"}
    ]
  },
  "repos": [
    {
      "url": "https://github.com/linktrend/LiNKskills",
      "startingRef": "issue/<issue>-<slug>"
    }
  ],
  "autoCreatePR": false,
  "workOnCurrentBranch": false
}
```

Complete non-secret template for the first Grok worker, ENV-00:

```json
{
  "packet_id": "LINKSKILLS-ENV-00-V1",
  "owner": "01a089cb-ee73-7c52-9e62-4f9654114eba",
  "repository": "linktrend/LiNKskills",
  "ref": "issue/<created-issue>-pin-cloud-execution-environment",
  "commit": "<40-char GitHub branch HEAD after inputs are pushed>",
  "tree": "<40-char tree for that commit>",
  "prompt": "Execute ENV-00 from docs/end-to-end-delivery/WORK-PACKETS.md at this exact identity. Do not broaden scope.",
  "allowed_paths": [
    "requirements-dev.txt",
    "requirements-dev.lock",
    ".github/workflows/ci.yml",
    "docs/development/CLOUD-EXECUTION.md",
    "tests/environment/"
  ],
  "acceptance_commands": [
    "python -m pip install --require-hashes -r requirements-dev.lock",
    "python3 validator.py --repo-root . --scan-all",
    "python3 -m pytest -q tests/environment",
    "git diff --check"
  ],
  "role": "implementation",
  "admitted": false,
  "admission_evidence": "<exact APPROVE and XP-00 admission receipt>"
}
```

`admitted` changes to `true` only after the referenced approval/admission exists.
The coordinator creates the issue branch through the installed repository
tooling, commits/pushes the plan and inputs, then fills identities with:

```bash
python3 scripts/gitops/create_issue_branch.py \
  --repo linktrend/LiNKskills \
  --workdir /Users/linktrend/Projects/LiNKskills \
  --prefer-worktree \
  'Pin the reproducible LiNKskills cloud execution environment'
REF='issue/<created-issue>-pin-cloud-execution-environment'
COMMIT="$(gh api "repos/linktrend/LiNKskills/git/ref/heads/${REF}" --jq '.object.sha')"
TREE="$(gh api "repos/linktrend/LiNKskills/git/commits/${COMMIT}" --jq '.tree.sha')"
python3 '/Users/linktrend/Documents/Codex/2026-09-09/files-pasted-by-the-user-i/outputs/cursor-cloud/cursor_cloud.py' validate '/absolute/path/to/LINKSKILLS-ENV-00-V1.json'
python3 '/Users/linktrend/Documents/Codex/2026-09-09/files-pasted-by-the-user-i/outputs/cursor-cloud/cursor_cloud.py' submit '/absolute/path/to/LINKSKILLS-ENV-00-V1.json'
python3 '/Users/linktrend/Documents/Codex/2026-09-09/files-pasted-by-the-user-i/outputs/cursor-cloud/cursor_cloud.py' watch LINKSKILLS-ENV-00-V1 --seconds 45
```

The packet JSON path is resolved inside the new governed LiNKskills issue
worktree. Stable packet IDs are never recycled with different content. Any
ambiguous create is reconciled through the saved agent identity and provider GET
before retry.

Saved Cursor environments are cache preparation only; they are never repository
or candidate authority. Cursor CLI login is also not authority for this route.

## Status, result, checkpoint, and handoff

The dispatcher persists the stable packet/agent identity before creation,
prevents a blind retry after an uncertain response, reads back
`GET /v1/agents/{agent-id}`, and verifies the cloud environment, repository
binding, available starting ref, and both PR flags. `poll`/`watch` retrieve the
latest run through `GET /v1/agents/{agent-id}/runs/{run-id}` and return terminal
status/result without model resampling.

Cursor's agent readback may omit the starting branch, so transport verification
is insufficient. The worker must first attest the requested origin, fetched
branch, exact HEAD commit/tree, clean workspace, and required toolchain. Any
mismatch fails closed. A completed Cursor run is only evidence to inspect.

An accepted worker commits and pushes its checkpoint to the exact `issue/*`
branch. An independent reviewer binds its verdict to that pushed commit/tree.
The Phase Packager/Coordinator creates the Phase PR; the delivery controller
alone may merge to protected `development`. Implementers do not create PRs,
self-review, merge, promote, or deploy.

## First executable packet after approval

`ED-00` is the exact immediately executable packet after `APPROVE`. It is a
bounded, no-provider-cost refresh that freezes protected LiNKskills and Platform
identities, the installed protocol/control digests, current Server 01 truth,
and all acceptance interfaces. Its source inputs are committed in this package.
It uses the founder Gate-0 route: Codex CLI with GPT-5.6 Luna High.

`ENV-00` is the first Grok worker packet. Once ED-00 accepts the refreshed
baseline, the coordinator precreates its owned GitHub issue branch, commits and
pushes every referenced input, obtains a current-task queue ownership receipt,
performs the one safe route preflight above, and dispatches through the pinned
REST route. `ED-01` follows its accepted reproducible-environment checkpoint;
its source/migration package does not need live Platform mutation, while live
application still waits for XP-01. Until the ownership receipt exists, ENV-00
and ED-01 are not executable now.

Luna High is not an automatic substitute for ordinary work. After Gate 0 it may
replace the direct Cursor route only on explicit Principal instruction, using
the same repository/ref/commit/tree, checkpoint, review, and protected delivery
controls.

## Cloud runtime and dependency start

The protected CI manifest is Ubuntu 24.04 ARM with Python 3.11. The completed
cloud qualification observed Linux x86_64, Python 3.12.3, Node 22.14.0, 4 vCPU,
and 15 GiB RAM. Python 3.12 satisfies the repository's `>=3.11` declarations,
but CI remains the ARM/Python 3.11 compatibility authority. The cloud image
initially lacked `ensurepip`; its disposable setup required
`python3.12-venv` and `python3.12-dev`.

The repository has no submodules or Node package manifest. Node/package-manager
setup is therefore irrelevant to ENV-00 and current Python packets. External
Python dependencies come from public PyPI; eight installable local packages
must be installed before the umbrella package, while `packages/contracts` and
`packages/persistence` remain `PYTHONPATH`-only. There is no current lockfile:
range-only `requirements-dev.txt` is the reason ENV-00 is the first Grok worker.
It creates the exact-version/hash lock and proves a fresh `--require-hashes`
install without adding a product dependency. Production data, GSM values, and
Server 01 credentials never enter the cloud VM.

## Permissions and unattended feasibility

The verified route can read the account/model/repository catalogue without an
interactive prompt. After the approved owner transition it can create and read
cloud agents through the REST API; the connected GitHub integration can fetch
and push an existing issue branch. It cannot create the GitHub issue, publish
privileged checks, merge protected branches, or deploy. Those remain supported
coordinator/controller operations. The worker prompt limits mutation to its
allowed paths and forbids nested dispatch, secrets, production access, PR
creation, merge, and deployment. Enforced tool denial remains authoritative
even after founder approval.

## Integration and deployment route

The current task collects pushed checkpoints. A provider-independent reviewer
reviews the exact commit/tree. The existing Phase Packager/Coordinator creates
logical Phase PRs; the delivery controller publishes required checks and merges
to `development`. Principal-controlled promotion uses existing temporary PRs to
`staging` and `main`.

ED-06 hands an immutable `docker.io/linktrend/linkskills@sha256:<digest>` image
to the active Platform/Server 01 owner. Registry pull is demonstrated by the
current deployment; registry write access is reverified after approval before
build/push and is not yet claimed. Coordinator SSH is
`linktrend@linkserver-01` using the existing named key; workers receive neither
SSH nor registry/runtime credentials. ED-08 reuses service
`linktrend-linkskills`, loopback host port `18798` to container `8787`, the
private core network, current 2 CPU/2 GiB envelope, and existing runtime-secret
mounts. Read-only inspection found 153,625,544 KiB free on `/srv` (40% used).
Before pull, require free space of at least the larger of 5 GiB or three times
the candidate's unpacked size, so candidate, rollback image, and temporary
layers coexist. Preserve the current image digest for rollback. XP-01 alone
owns shared database migration, backup/restore, PACI/
service identity, runtime SecretRefs, and concurrent migration exclusion.

The only unavoidable founder action before work is literal `APPROVE`. A new
purchase, account consent, model substitution, broadened initial Skill set,
live deployment/provider mutation, or production acceptance returns to the
founder. Ordinary issue creation, narrow owner-map transition, environment
setup, artifact preparation, testing, and checkpoint delivery are scheduled
execution steps and do not create additional founder decisions.

## Later live prerequisites

- XP-01: Platform database, migrations, identity, backup/restore, worker, and
  runtime receipts before live store/auth/publication/deployment.
- XP-02: shared/global Cursor configuration only if ED-05/09 cannot remain
  project-scoped.
- XP-03: Codex consumer owner applies and proves its exact pin.
- XP-04: Lisa/OpenClaw owner applies and proves its exact pin.
- Founder-reserved gates: live provider mutation, Server 01 deployment,
  production acceptance, and any change of model route or initial skill set.

Planning/interface maturity and an executable coordinator route do not satisfy
these later production prerequisites.
