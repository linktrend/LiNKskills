# PKT-00 / ISS-00 Architecture Approval Record

- **Observed:** 2026-08-24 (Asia/Taipei)
- **Packet:** PKT-00 — Baseline reconciliation and architecture approvals
- **Issue:** ISS-00 — Reconcile exact baseline and approve architecture changes
- **Execution state:** `PLAN`
- **Product implementation state:** `NOT AUTHORIZED BY THIS RECORD`
- **Companion inventory:** [`../../inventories/governed-skill-expansion-baseline-2026-08-24.md`](../../inventories/governed-skill-expansion-baseline-2026-08-24.md)

## Approval identity

The planning manifest remains the identity authority for this packet. Its SHA-256 is
`c14c3ccdb612d9bee2be2a4d4ff71358e98cff63e6f09c9f58ac9e49816e7263`, bound to
manifest baseline commit `2896fd89726f0b20258ec5a7bba55ccc6299ceb6` and tree
`727694a95c83678bd6c7be7da2c5b26127b49e6e`. The current `origin/development` tip is
the descendant `91970bbb273acd12a643c722608ded33e42ae7e` / tree
`5312f355243bda6452422a262e18135cb2c07372`. The routing matrix and successor remain
unchanged and are not edited by PKT-00.

No literal Principal `APPROVED` record bound to this manifest digest is present in
the committed planning package. Therefore this record documents architecture and
reserved-action holds; it does not manufacture dispatch authority. The orchestrator
must obtain and record that approval before PKT-01 begins, after resolving the
baseline/receipt identity mismatch described in the inventory.

## Durable decision table

| Decision | Single authority | Decision recorded | Implementation state | Reserved gate |
|---|---|---|---|---|
| Provider-v2 uses standard MCP negotiation, bounded family-first discovery, and exact immutable release resources | ADR 0003 amendment | [`docs/adr/0003-protocol-independent-core-mcp-api.md`](../../adr/0003-protocol-independent-core-mcp-api.md) | Architecture direction only | Protocol/provider migration requires explicit approval and rollback evidence |
| Consumers retrieve and verify exact releases, then execute locally; provider-side `skills_run_*` / `skills_tool_*` is not the v2 authority | ADR 0003 amendment + OpenClaw handoff | ADR 0003; [`docs/integrations/openclaw/HANDOFF.md`](../../integrations/openclaw/HANDOFF.md) | Architecture direction only | Consumer implementation and canary remain OpenClaw-owned |
| External material is immutable vendor lineage; adaptations are separate linked releases | ADR 0002 amendment | [`docs/adr/0002-git-source-and-platform-publication.md`](../../adr/0002-git-source-and-platform-publication.md) | Architecture direction only | Import, licence review, and publication require PKT-01/03 evidence |
| Upstream updates are signed idempotent candidates and never auto-promote/current-switch | ADR 0002 amendment + ADR 0008 Librarian boundary | ADR 0002; [`docs/adr/0008-librarian-ownership-cross-repo-contract.md`](../../adr/0008-librarian-ownership-cross-repo-contract.md) | Architecture direction only | LiNKautowork polling and Platform host operations remain external handoffs |
| LiNKskills owns catalogue/release/provider metadata; Platform owns identity/live migrations/host; OpenClaw owns local execution/private state | Existing ownership matrix and ADRs 0001/0002/0003/0008 | [`docs/inventories/ownership-matrix.md`](../../inventories/ownership-matrix.md), [`docs/inventories/cross-plan-interface-gates.md`](../../inventories/cross-plan-interface-gates.md) | Reaffirmed | Cross-repository gates cannot be bypassed |

## Blast-radius register

PKT-00 changes no runtime behavior. The following downstream surfaces are identified
for later packets and remain held until their owners provide their own evidence:

| Surface | Owning packet/repository | Change anticipated | Required proof before action |
|---|---|---|---|
| Taxonomy, collection, provenance, eligibility, role-pack schemas | PKT-01 / LiNKskills | Additive versioned contracts and fixtures | Schema validation, positive/negative fixtures, compatibility report |
| Standard MCP v2 provider and exact resource reads | PKT-02 / LiNKskills | Provider adapter and conformance tests | MCP transcript, bounded pagination, exact byte/digest receipt, denial tests |
| Vendor/adaptation/update lifecycle and migrations | PKT-03 / LiNKskills + LiNKplatform | Additive metadata, candidate/review transitions, migration package | Idempotency, provenance, rollback, Platform review/apply receipt; no independent live apply |
| Imported-content security/privacy and Librarian qualification | PKT-04 / LiNKskills | Adversarial fixtures, telemetry constraints, review controls | Privacy-negative and qualification refusal evidence |
| Google Workspace complete collection | PKT-05 / LiNKskills + consumer owner | Mechanical inventory and immutable collection manifest | Exact upstream pin, licence/integrity/security review, inactive default |
| OpenClaw v2 consumer/canary | XPKT-02/XPKT-04 / OpenClaw Prime | Local retrieval/execution and instance bindings | Consumer-local digest proof, profile/tool authority, rollback; no future-agent activation |
| Identity, migrations, generic Librarian host | XPKT-01 / LiNKplatform | Review/apply/integrate external contracts | Platform-owned claim/migration/host receipts |
| Upstream polling | XPKT-03 / LiNKautowork | Deterministic candidate submission | Signed idempotent candidate proof; no qualification/promotion |
| Stage/VPS/E2E/production | XPKT-04/XPKT-05 / named owners | Separate deployment/canary proof | Exact environment/source/consumer/rollback receipts and explicit approvals |

## Approval and rollback state

| Gate | State at PKT-00 checkpoint | Required next action |
|---|---|---|
| Documentation-only architecture amendments | `RECORDED — PROPOSED` | Principal/orchestrator reviews this record |
| Manifest digest and routing receipt | `VALID FOR PLAN; BASELINE STALE AGAINST REMOTE TIP` | Refresh identity and issue a new receipt, or obtain explicit approval for the older manifest baseline |
| Founder approval for PKT-01 and reserved schema/protocol/migration work | `HOLD — NOT RECORDED HERE` | Record literal `APPROVED` bound to the final manifest digest before PKT-01 |
| Runtime, migration, publication, deployment, activation, and promotion | `HOLD` | Separate owner and action-specific approval/evidence |

Rollback for this packet is a documentation revert. No runtime state, immutable
release, migration, consumer configuration, or routing authority is changed.
