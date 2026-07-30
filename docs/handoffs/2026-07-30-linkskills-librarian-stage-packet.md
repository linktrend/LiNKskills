# LiNKskills Librarian domain worker — stage packet (Skills-owned)

**Status:** Skills package + fake-host proof ready; **live host integration is Platform-owned**  
**Date:** 2026-07-30 (Asia/Taipei)  
**Contract:** `docs/contracts/librarian-domain-worker-v0.1.md` (v0.1)  
**Platform host ADR (read-only ref):** LiNKplatform `docs/adr/0008-generic-librarian-worker-host.md`  
**Skills package:** `packages/librarian_domain/` (`linkskills_librarian`)

## Ownership boundary (hard)

| Asset | Owner |
|---|---|
| Domain worker package, policies, store, conformance fixtures, this packet | **LiNKskills** |
| Generic Librarian host loading, scheduling, credentials, audit/alerts, shared runner files | **LiNKplatform** |
| Live migrate / deploy / enable Skills worker on stage/prod | **LiNKplatform alone** |

LiNKskills agents must **not** edit LiNKplatform shared runner files or apply live shared migrations.

## Skills-owned worker identity / config

| Field | Value |
|---|---|
| Domain workflow key | `linkskills` |
| Worker version | `0.1` (`WORKER_VERSION`) |
| Package import | `linkskills_librarian` |
| Entrypoint class | `DomainWorker` |
| Fake host harness | `FakeLibrarianHost` |
| Runtime principal (name only) | `svc_lskills_librarian` — Platform-issued; never actor-distributed |
| Contract path | `docs/contracts/librarian-domain-worker-v0.1.md` |

### Logical operations (v0.1 surface)

Implemented domain methods (see `packages/librarian_domain/linkskills_librarian/worker.py`):

- `intake_normalize`
- `prioritize`
- `propose_improvement` (refuses staging/main direct push)
- `request_eval` (requires executed evidence)
- `interpret_eval_evidence` (receipt-bound via `evaluate_certification_evidence`; prompt-only never certifies)
- `propose_consolidation` (low-confidence escalates to review queue)
- `enqueue_review`

Host scheduling, retries, DLQ, secret injection, and enable/disable remain Platform host concerns.

## Migration refs (packaged; apply authority = Platform)

See `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md`. Skills ships SQL; **Platform applies live**.

| Order | File | SHA-256 |
|---|---|---|
| 1 | `supabase/migrations/20260715_000002_lskills_catalog_core.sql` | `4991dd628cc501a1013a4d7c3d8f859274e62ff847e768f106b0e3c2b89d8414` |
| 2 | `supabase/migrations/20260715_000003_lskills_catalog_seed.sql` | `5e8f58a7159ad09f0c6389e12060c6a9cc76ff73dcfc2397ddea256d47a75e82` |
| 3 | `supabase/migrations/20260718_000004_lskills_postgrest_exposure.sql` | `4220d70b626313f572a38720958fb78550b3b89c0efab5366a449d33c0b22ca0` |
| 4 | `supabase/migrations/20260727_000005_lskills_registry_foundation.sql` | `36081765032f21dfd2dcca223035555e1e54b71298874235def8e0362c55c4ed` |
| 5 | `supabase/migrations/20260728_000006_lskills_rls_actor_org_scope.sql` | `12c2e45e94fd9216a5857ce53ce299a953dc2ee869f89bcdb392857133df763d` |

Also requires Platform foundation (`platform.organizations`, role helpers) already present.

## Fake-host proof commands (local only)

Evidence class: **local/fake**. Does not prove live host integration.

```bash
cd /path/to/LiNKskills
PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:." \
  python3 -m unittest discover -s tests/librarian_domain -v
```

**Recorded 2026-07-30 (this session):** 9 tests OK (`ConformanceTests`, `WorkerPolicyTests`, `LibrarianStoreTests`) in ~0.018s.

Optional interactive smoke:

```bash
PYTHONPATH="packages/librarian_domain:packages/core:." python3 - <<'PY'
from linkskills_librarian import DomainWorker, FakeLibrarianHost, DEFAULT_FIXTURES
host = FakeLibrarianHost(DomainWorker())
print(host.run_fixture_suite(DEFAULT_FIXTURES)["invocation_count"])
PY
```

## Health / smoke expectations (for Platform host wiring)

Skills-side health signals Platform should expose after loading the versioned worker:

1. Worker package importable; `DomainWorker().version == "0.1"` and `domain_key == "linkskills"`.
2. Fake/conformance fixtures succeed in host CI or Skills-reported unit proof (above).
3. `interpret_eval_evidence` rejects prompt-only / thin case_results without sealed receipts.
4. Protected-branch proposals (`staging`/`main` push) are refused.
5. Review queue enqueue works (memory or configured store path).

Live DB row counts (`lskills.catalog` ≥ 34, registry tables present) are **stage gates after Platform apply** — not claimed here.

## Rollback (Skills package)

| Layer | Rollback |
|---|---|
| Skills domain package | Pin prior worker package version / git SHA; host disables `linkskills` worker |
| Host schedule | Platform pause/disable Skills worker only (Brain must remain independently operable per Platform ADR 0008) |
| Migrations | Platform-owned down migration for additive tables only — never `drop schema lskills cascade` from Skills |
| Classification | Remain `draft` — no usable promotion to roll back |

## Versioned handoff for Platform generic host

Deliverables for LiNKplatform (consume; do not edit from Skills):

1. This packet + contract v0.1.
2. Package `packages/librarian_domain/` at a pinned Skills commit SHA (fill when Platform integrates).
3. Fake fixtures: `DEFAULT_FIXTURES` + `FakeLibrarianHost`.
4. Required credential **names only:** `svc_lskills_librarian` (+ Platform secret injection for host DB/GSM).
5. Evidence rule: certification recommendations require sealed Eval Runner receipts; prompt-only is schema-invalid.
6. Failure taxonomy (domain): policy refuse, evidence hold (`hold_eval_pending`), consolidation escalate-to-review.

**Live host integration status:** **blocked / Platform-owned.** Skills has not started multi-day canaries and does not invent stage endpoints.

## Explicit non-claims

- No live Librarian schedule on stage/prod from this packet.
- No Brain worker changes.
- No sibling-repo edits.
- No sealed live skill certification promotions (see `evidence/phase10/`).
