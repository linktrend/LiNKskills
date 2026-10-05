# Agent Workforce Evaluation Benchmark Register Design

## Task distinction and deliverable

Design a versioned, typed benchmark register and export contract for reporting comparable agent runs. This is a data-model/artifact task; it does not design or execute the evaluation itself. Use [`agent-workforce-evaluation`](../../agent-workforce-evaluation/SKILL.md) for case design, authorized execution or analysis of actual run results. The register skill defines fields, denominator semantics, export formats, validation rules, and a synthetic worked example.

## Method

1. **Fix identity and comparability.** Define stable run ID; agent and exact model/build/version; task suite ID/version and case set hash; evaluator/grader version; runtime/environment; run mode; date; baseline identity; owner; and declared tool/policy configuration. Never compare rows whose identity, scope, or suite semantics differ without an explicit caveat.
2. **Model observations, not claims.** Keep counts for planned, attempted, completed, passed, failed, skipped, and unrun cases. Require `attempted = passed + failed` when every attempted case receives a binary outcome; preserve `unscored` separately. A pass-rate denominator uses only scored attempts and is labelled. For a 10-case run with 7 pass, 1 fail, and 2 unrun, attempted/scored denominator is 8 and pass rate is 7/8 = 87.5%, not 70%.
3. **Separate metrics and denominators.** Store raw counts and derived ratios separately. Tool-call precision requires a declared expected/valid invocation denominator; in the supplied example, 1 invalid out of 20 calls gives invalid-call rate = 5%. Tokens require units and aggregation rule. Cost requires exact currency, observed cost source or supplied price schedule, and coverage; never infer current model prices. Cost per solved case is total measured cost / solved cases only when solved > 0. For $2.80 and 7 solved, it is $0.40 per solved case. If solved is zero, report null/not-defined.
4. **Encode typed fields.** Produce a neutral field dictionary plus JSON Schema and CSV columns. SQL DDL is only a proposed schema artifact; do not apply migrations or assume a database dialect. Use explicit enum sets and units, ISO date, nullable/missing semantics, bounds, and provenance for every computed field. Avoid model/suite enums copied from the source because those examples are dated and task-specific; permit versioned registry IDs instead.
5. **Define comparison policy.** Baseline comparisons require same suite/version, task distribution, scoring rules, and environment or a documented difference. Use absolute delta and relative delta with explicit zero-baseline handling. A regression verdict is a policy label produced from owner-supplied threshold, never a field the author guesses. Preserve per-case outcomes so aggregate masking is visible.
6. **Validate and hand off.** Check schema syntax, field/type parity among JSON/CSV/SQL proposal, IDs/hashes, date/currency units, arithmetic invariants, unique run IDs, and source links. Create only requested local draft files through native `write`; no write to Notion, SQL, CI, evaluation system or catalog.

## Worked synthetic register row

Input: suite has 10 cases; 7 pass, 1 fail, 2 unrun; 20 observed tool calls with 1 invalid call; 2.80 USD measured total cost; 7 solved cases. Output: `planned=10`, `attempted=8`, `passed=7`, `failed=1`, `unrun=2`, `pass_rate=0.875`, `tool_calls=20`, `invalid_calls=1`, `invalid_call_rate=0.05`, `total_cost=2.80`, `currency=USD`, `solved=7`, `cost_per_solved=0.40`. Mark run evidence source and measurement policy; do not imply this fictional result is real.

## Failure checks

- Reject or flag attempts inconsistent with pass+fail+unscored counts.
- Keep missing measurements null with reason, never zero.
- Set ratio undefined if denominator is zero.
- Preserve exact run identity and source hashes; refuse an unsupported current price lookup or guessed provider.
- If a CSV export loses types, include data dictionary and JSON Schema as controlling contract.

## Native interface and authority

Use native `read` for supplied evidence and native `write`/`edit` for a requested internal specification. Do not use SQL, shell, Notion, CI, or benchmark-service connectors unless a current owner-supported schema explicitly authorizes a read-only operation; this skill never creates or mutates those systems. Runtime checkpoint persistence is consumer-owned, not a JSONL file.
