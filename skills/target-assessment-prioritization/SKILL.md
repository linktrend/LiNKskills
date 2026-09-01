---
name: target-assessment-prioritization
description: "Evidence-bounded assessment and deterministic prioritization of supplied target candidates using declared criteria, uncertainty, and owner-review recommendations without selection or LiNKtarget mutation."
usage_trigger: "Use when supplied synthetic, redacted, or public target candidates need a transparent assessment or deterministic priority draft based only on declared, evidence-backed criteria."
version: 0.1.0
release_tag: v0.1.0
created: 2026-09-01
author: LiNKskills Library
tags: [targeting, assessment, prioritization, evidence, ranking]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5.6-luna
  context_required: 128000
tools: [read_file, list_dir, get_tool_details]
dependencies: [target-definition-segmentation]
permissions: [fs_read]
scope_out: ["No publication or certification claim", "No Program authority or live Platform use", "No target selection, activation, contact, connector call, or LiNKtarget mutation", "No invented evidence, sensitive-trait inference, or private-data retention"]
format_profile: simple
persistence:
  required: false
  state_model: stateless_single_pass
last_updated: 2026-09-01
---

# Target Assessment and Prioritization

Evidence-bounded assessment and deterministic prioritization of supplied target candidates using declared criteria, uncertainty, and owner-review recommendations without selection or LiNKtarget mutation. This is a source-only review method. It does not define the source population, select or contact a target, activate a priority, publish a ranking, grant authority, call a connector, or create or mutate LiNKtarget state.

## Compact contract

1. Accept only a named synthetic, redacted, or public source population and explicit evidence references.
2. Apply only declared criteria. Record `met`, `not_met`, or `unknown`; never infer missing or sensitive attributes.
3. Keep exclusions, uncertainty, and the exact `Other — specify` escape hatch visible.
4. Produce only `READY_FOR_OWNER`, `DRAFT`, or `BLOCKED`, with empty messages, external calls, selections, and mutations.
5. Treat every result as a non-selectable owner-review draft. It is not published, certified, authorized by a Program, or active in the Platform.

## Progressive disclosure

- **Level 1 — route:** use this summary to decide whether the supplied matter matches the skill.
- **Level 2 — apply:** read [`advanced/advanced.md`](advanced/advanced.md) for criterion, uncertainty, ordering, and refusal rules.
- **Level 3 — integrate:** read [`references/schemas.json`](references/schemas.json), [`references/skill-pack.json`](references/skill-pack.json), and [`references/eval-suite.json`](references/eval-suite.json) before adapting a consumer.
- **Level 4 — verify:** run the deterministic package tests and review [`references/catalog-fragment.json`](references/catalog-fragment.json). The fragment is a draft discovery input, not publication or certification.

## Global ineligibility

This package is **globally ineligible and non-selectable**. Its lifecycle and certification states are `draft` and `uncertified`. A consumer must not interpret package presence, an evaluation fixture, a catalog entry, or `READY_FOR_OWNER` as publication, certification, Program authority, live Platform availability, or permission to mutate LiNKtarget.
