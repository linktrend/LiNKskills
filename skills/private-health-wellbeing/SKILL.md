---
name: private-health-wellbeing
description: "A private-domain health tracking and reporting method that preserves not-reported values, separates routine measures, labels estimates, and exposes only an optional capacity state."
usage_trigger: "Use for a synthetic or redacted private health tracking, checkpoint, measurement, nutrition, sleep, treatment/appointment, or image-correction request without diagnosing, changing treatment, or exporting detailed health data."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-24
author: LiNKskills Library
tags: [private-health, wellbeing, tracking, privacy, evidence]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["Do not diagnose, triage, prescribe, recommend a treatment change, or provide medical emergency instructions", "Do not retain or expose real personal health data, images, credentials, or private records in releases, fixtures, telemetry, or subordinate access", "Do not send detailed health data outside the private consumer store; only an explicitly requested capacity state may be exported", "Do not call a calendar, health, image, messaging, or clinical service, create reminders, or mutate treatment, appointment, device, or measurement records"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-08-24
---

# Private Health and Wellbeing

This skill is a private consumer-side tracking and reporting method. It
organizes synthetic or redacted observations and produces an evidence-labeled
draft; it is not a clinician, diagnostic system, treatment planner, emergency
service, calendar connector, image store, or system of record.

## Safety and privacy gate

1. Accept only `synthetic` or `redacted_private_snapshot` input. Refuse live
   personal identifiers, unredacted photos, credentials, and private records.
2. Require a source reference and explicit status for each material observation.
   Use `not_reported` rather than guessing, filling, or repeating a known
   answer. A request that repeats a known field is rejected as redundant.
3. Keep detailed energy, mood, stress, sleep, hydration, nutrition, treatment,
   image, bowel, waist, and device observations in the private consumer store.
   The only exportable summary is an explicitly requested capacity state.
4. Never diagnose, infer a disease, recommend a treatment or dose change, or
   claim that a measurement is clinically meaningful. Treatment and appointment
   mode records a supplied fact or question for owner review only.
5. Never implement or emit the rejected stock wording about guiding someone
   toward human or emergency support. If a safety concern is supplied, mark it
   `PENDING_REVIEW` and name the owner-defined review channel without inventing
   emergency instructions.

## Supported records

- Initial and monthly assessments preserve missing fields as `not_reported`.
- Three routine checkpoints keep energy, mood, and stress as separate 1–5
  values and record capacity independently.
- Hydration calculates a non-negative bottle/remaining difference only when
  both measurements and units are supplied. It never creates a reminder.
- Treatment and appointment mode records a supplied appointment or dose fact;
  combined dose and dose-change requests are always owner-review items.
- Nutrition and meal/photo records label estimates and image uncertainty;
  protein estimates are labeled, and correction records preserve the original uncertainty rather than rewriting
  history.
- Exercise proposals require cited evidence, avoid spot-reduction claims, and
  remain proposals. Sleep duration is a transparent time calculation.
- Weight/scale, waist, and bowel records retain their separate device/source
  or observation provenance. No category is silently merged.

## Tool, state, and transport boundary

Use native CLI first, a CLI wrapper for deterministic normalization, and the
offline helper second. A direct API is allowed only through a consumer-owned
exception adapter, and MCP is allowed only when the consumer has separately
authorized a persistent session. Inspect any specialist/generalist or
more-than-ten-tool capability with `get_tool_details`; retain only capability
summaries. The helper never calls a service, writes outside task-local state,
sets calendar reminders, sends a message, uploads an image, or changes a
 treatment. Consumers own private storage, bindings, transport, retention,
access control, and any qualified clinical review.

Every completed draft carries source evidence, uncertainty, a private
destination contract, empty external effects, and an exact rollback reference.
Incomplete, unsafe, redundant, or unknown requests fail closed.

## Contracts and progressive disclosure

The input, output, and state contracts are in
[`references/schemas.json`](references/schemas.json) (input:
`references/schemas.json#/definitions/input`; output:
`references/schemas.json#/definitions/output`; state:
`references/schemas.json#/definitions/state`). Read the field-level
rules in [`advanced/advanced.md`](advanced/advanced.md), the private-source
and destination record in [`references/api-specs.md`](references/api-specs.md),
the synthetic examples, `old-patterns.md`, and the canonical eval suite before
release. The exact runtime profile is stamped only after all canonical files
are final.
