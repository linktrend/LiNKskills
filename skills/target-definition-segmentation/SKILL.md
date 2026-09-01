---
name: target-definition-segmentation
description: "Evidence-bounded target definition and segmentation for explicit populations, criteria, exclusions, uncertainty, and owner-reviewed segment drafts without selecting records or mutating LiNKtarget."
usage_trigger: "Use when supplied synthetic, redacted, or public evidence needs a reviewable target definition or segment draft with explicit inclusion, exclusion, evidence, and uncertainty boundaries."
version: 0.1.0
release_tag: v0.1.0
created: 2026-09-01
author: LiNKskills Library
tags: [targeting, segmentation, criteria, evidence, privacy]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5.6-luna
  context_required: 128000
tools: [read_file, list_dir, get_tool_details]
dependencies: [target-assessment-prioritization]
permissions: [fs_read]
scope_out: ["No publication or certification claim", "No Program authority or live Platform use", "No target selection, activation, contact, connector call, or LiNKtarget mutation", "No invented evidence, sensitive-trait inference, or private-data retention"]
format_profile: simple
persistence:
  required: false
  state_model: stateless_single_pass
last_updated: 2026-09-01
---

# Target Definition and Segmentation

Evidence-bounded target definition and segmentation for explicit populations, criteria, exclusions, uncertainty, and owner-reviewed segment drafts without selecting records or mutating LiNKtarget. This is a source-only review method. It does not select people or accounts, score or rank targets, activate a segment, publish an audience, grant authority, call a connector, or create or mutate LiNKtarget state.

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
