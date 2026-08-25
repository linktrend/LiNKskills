# Requirements Traceability

This matrix prevents requirement loss and duplicate implementation. Packet completion is necessary but not sufficient: PKT-26 independently checks the stated proof level.

| Requirement group | Existing capability reused | Gap-closing packets | Required proof |
|---|---|---|---|
| Ownership and non-duplication | ADRs 0001–0009; provider/release foundations | PKT-00, PKT-24, PKT-26 | Ownership matrix, overlap/supersession ledger, independent reconciliation |
| Family-first progressive discovery | ADR 0004 levels 0–6; v2 resource names | PKT-01, PKT-02, XPKT-02 | Family/category pagination, bounded context, three-gate denial, OpenClaw transcript |
| Exact immutable retrieval | release-v2 digests, attestation, dependency closure | PKT-02, PKT-25, XPKT-02 | Byte/digest equality, lifecycle denial, local verification receipt |
| External collection lifecycle | publisher, persistence, Librarian review foundations | PKT-01, PKT-03, PKT-04, XPKT-03 | Vendor immutability, linked adaptation, idempotent proposal, review outcomes, rollback |
| Google complete collection | `gws` wrapper and historical vendored snapshot | PKT-05, PKT-23, PKT-24 | Mechanical inventory, pin/licence/security/digests, inactive default, subset eligibility |
| Research | `search-strategy`, `citation-enforcer` | PKT-06 | Source review, overlap migration, currentness/conflict/injection/privacy evals |
| Governed browser use | narrow `ui-ux-guardian` visual checks only | PKT-07, XPKT-02 | Action-class/approval/credential/download/network/uncertainty denials |
| Company communication | reusable style primitives in existing skills | PKT-08 | Audience, mobile, choice, uncertainty, evidence, no-emoji evals |
| Operational Reporting | `executive-sync-8am`, `studio-health-reporting` migration inputs | PKT-09 | All modes, verified-only content, omission/no-change, battery-line, migration mapping |
| Personal Compliance | no complete equivalent | PKT-10 | Selfie state machine, adaptive rates/projections, silent checks, image correction, privacy |
| Time Management | `department-head`, `task-decomposition` inputs | PKT-11, XPKT-02 | Intake/status/planning/evidence/capacity/standing-rule scenarios and SQLite ownership |
| Private Health and Wellbeing | no equivalent | PKT-12, XPKT-02 | Full category/checkpoint coverage, private-store boundary, synthetic fixtures, wording prohibition |
| Executive decisions/governance | executive/supervision primitives | PKT-13 | Decision brief, choices, rule impact, implementation tracking, authority denial |
| Company planning/performance | decomposition/reporting primitives | PKT-14 | Horizon/KPI/forecast/actual/blocker/obsolete/reprioritization evals |
| Finance/accounting/Odoo | `studio-controller` input; approved Odoo system | PKT-15 | External-source review, Odoo contract, finance workflows, connector/credential exclusions |
| Sales/customer/Odoo | marketing/market primitives; Odoo and LiNKreach boundaries | PKT-16 | Pipeline/onboarding/renewal/risk evals and ownership denials |
| Contracts/legal | compliance/citation primitives | PKT-17 | Jurisdiction/evidence/playbook/escalation and no-final-authority evals |
| Meetings | research/task/reporting primitives | PKT-18 | Agenda/brief/notes/decisions/routing/follow-up and transcript privacy |
| Procurement/vendor | research/legal/decision primitives | PKT-19 | Supplier/pricing/renewal/performance/continuity/approval evals |
| Agent workforce | department supervision/delegation primitives | PKT-20 | Role/rule/capability/delegation/evidence/failure/suspend flows and authority denial |
| Incident/continuity | devops/audit/blocker primitives | PKT-21 | Incident/recovery/communication/closure evidence and owning-system boundaries |
| Role packs | exact releases and dependency closure | PKT-22 | Exact qualified references, capability classes, no bodies/identity/activation/private data |
| Security/privacy/telemetry | telemetry-v2 privacy and eval runner | PKT-04, PKT-23, PKT-25 | Adversarial and privacy-negative suites, no raw private data, explicit effects |
| Librarian lifecycle | domain worker/review queue | PKT-03, PKT-04, XPKT-01 | Diff/recommendation/qualification/rollback and no direct production mutation |
| Platform migration/auth | existing claims/migration ownership contract | XPKT-01 | Exact migration/claims receipts; Skills/Brain separation |
| Upstream polling | LiNKautowork deterministic automation boundary | XPKT-03 | Signed idempotent candidates; no automatic qualification/promotion |
| Lisa/OpenClaw canary | existing native bridge and v2 scaffolding; exact values in `LISA-CANARY-BINDINGS.md` | XPKT-02, XPKT-04 | Exact authorized discovery/retrieval/local use, schedules/state/private mappings, rollback, no future-agent activation |
| Final definition of done | existing delivery/evidence controls | PKT-25, XPKT-05, PKT-26 | Separate source/consumer/stage/VPS/E2E/production classification with exact identities |

## Explicit exclusions trace

The following are never implemented as LiNKskills product capability in these packets: identity/credentials/RBAC; Brain knowledge/rule approval; schedules and delivery; private ledgers; OAuth/account bindings; browser binary/profile/cookies/network sandbox; Google CLI; Odoo server/connector; model-provider routing/runtime configuration; deterministic scheduler runtime; Program Ledger mutation; non-skill software; real private data; or future-agent activation. The companion model-routing matrix governs only which execution worker may implement or review each packet; it does not add model routing to the LiNKskills product.
