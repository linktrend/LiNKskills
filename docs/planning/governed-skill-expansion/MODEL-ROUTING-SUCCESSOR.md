# LiNKskills Governed Skill Expansion — Model-Routing Successor

**Status:** planning authority only; no product dispatch, execution, approval, or promotion is implied

**Scope:** the single `linkskills-governed-skill-expansion` execution manifest and its 27 LiNKskills packets

## Authority

This is the narrow Principal-authoritative successor to the earlier Sonnet/Sol-first planning default. Product scope, packet dependencies, owned paths, acceptance criteria, and repository ownership remain unchanged. The installed IDE v2.5.1 manifest schema has `additionalProperties: false` and no routing field, so the exact routing assignment is carried by a companion matrix and digest-bound receipt instead of an invalid manifest extension.

## Required routes

1. **AUTO COST** is the preferred general route. The only accepted selector is Cursor Router SDK `auto-smart` with `optimize_for=cost`. Generic Auto, Auto Balance, Auto Intelligence, Cloud API `default`, omitted selection, and an Auto label without effective-mode readback fail closed.
2. **Composer 2.5** uses `composer-2.5` with `fast=false` only when every bounded-work criterion is explicitly true: one repository, existing pattern, normally no more than five changed files, explicit requirements, no architecture or sensitive domain, obvious failure, objective verification, and easy rollback.
3. **Cursor Grok 4.6 Medium** uses `grok-4.6` with `effort=medium` and `fast=false` for complex, sensitive, context-heavy, or long-running work.
4. **Third-party models** are exceptions. This package binds Opus 4.8 Medium only to separate consequential independent review and GPT-5.6 Sol Medium only to a one-hop quality-recovery exception after Grok. Gemini and other third-party routes are not assigned.
5. **Fast is forbidden** on every route. Absence of a verifiable Fast=false capability/readback is a HOLD, not permission to infer non-Fast.

## Admission receipt

Before any subtask mutation, the orchestrator must retain:

- packet and subtask IDs, manifest digest, routing-matrix digest, and exact baseline commit/tree;
- intent `PREPARED` and no earlier mutation timestamp;
- requested route, stable model slug, transport, exact selection ID, and ordered parameters;
- returned effective model ID, display name, parameters/mode, provider family, usage pool, and Fast state;
- an attestation that Auto Cost returned `optimize_for=cost` when applicable;
- a provider-family comparison for any fallback or independent reviewer; and
- the separately assigned Terra checkpoint identity.

The current unauthenticated planning shell could identify Cursor Agent version `2026.08.11-e8db854`, but `agent models` correctly failed with `Authentication required`. No login, token, model call, or substitution was attempted. Therefore the matrix records exact requested selectors from the Principal-authoritative Cursor routing contract, while each route remains admission-HOLD until the authorized execution transport proves the live catalogue and effective readback.

## Failure and fallback controls

- Escalation is allowed only for `code_defect`, `quality_gate_failed`, or recurring `timeout_uncertain` attributable to model quality.
- The evidence log must contain attempt identity, exact model/readback, failure class, reason, and timestamp before the one-hop fallback starts.
- Infrastructure, authentication, capacity, transport, quota, repository, input, or tool failures do not change the model. Repair and retry the same route or HOLD.
- AUTO COST normally falls back to Grok. If AUTO COST's effective model is already xAI, use the matrix's different-family Sol quality-recovery exception instead; never create a same-family hop.
- Composer falls back once to Grok. Grok falls back once to Sol. Sol and independent-review failures surface to repair with no automatic second hop.
- A fallback is not a new default and does not amend later packet routing.

## Independent review and Terra separation

Opus independent review is a separate worker receiving the original request, approved scope, complete diff, tests, known risks, and author-route readback. It never authors the same subtask and never substitutes for checkpoint grading. Terra independently verifies each exact packet checkpoint and remains separate from both author and reviewer. A packet without a model reviewer still requires Terra checkpoint verification.

## Cost forecast

The package uses route-call units because live token volume and account pricing are execution-time facts. Baseline maximum before quality fallback is 27 author workers plus 16 independent-review workers. Eight author packets prefer AUTO COST, two use Composer, sixteen use Grok, and PKT-26 is the independent Opus reconciliation worker. No Gemini/bulk route is budgeted. Quality fallback is exceptional and capped at one extra author attempt per affected subtask; it is not pre-consumed capacity.

Third-party cost pools are limited to:

- `other:independent-review` — Opus on the 16 consequential review assignments, justified by provider-family-independent challenge; and
- `other:quality-recovery` — Sol only after a logged Grok or xAI-effective AUTO COST model-quality failure.

AUTO COST, Composer, and Grok use the Cursor pool. Every receipt records the returned usage pool so cost reporting is evidence-based rather than inferred.

## Acceptance controls

- the receipt hashes match the exact manifest and matrix bytes;
- all 27 packet IDs appear exactly once and match the manifest dependency set;
- every packet binds implementation, deterministic verification, independent-review disposition, and Terra checkpoint verification;
- no selector or parameter enables Fast;
- no generic or unverifiable Auto is accepted;
- AUTO COST uses a supported Cursor SDK/router transport or remains HOLD;
- every fallback is logged, different-family, one-hop, and model-quality-only;
- third-party use has a task-specific necessity and cost-pool reason;
- independent review uses a separate worker; and
- product implementation remains in `PLAN` until separate founder approval.
