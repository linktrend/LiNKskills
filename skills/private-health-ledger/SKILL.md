---
name: private-health-ledger
description: "Maintains a private, source-labelled health ledger and personal report while exposing only an approved coarse work-capacity signal."
usage_trigger: "Use when a consumer needs longitudinal tracking of treatment, medication, diet, exercise, sleep, mood, measurements, symptoms, or work capacity."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-19
author: LiNKskills Library
tags: [health, privacy, medication, wellbeing, capacity]
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
scope_out: ["Do not diagnose or change treatment", "Do not expose detailed health data to work systems or subordinate agents", "Do not guess missing observations or provide false reassurance"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
format_profile: heavy
last_updated: 2026-08-19
---

# Private Health Ledger

This is a reusable private-health workflow. The consuming Program supplies the
person, timezone, private store, checkpoint schedule, treatment facts,
measurement devices, report destination, and clinician boundary. Those values
must never be embedded in the shared skill or sent to LiNKbrain.

## Tooling protocol

Classify the request as `specialist` or `generalist`. Use native CLI first,
then a narrow CLI wrapper, then a direct API only for an approved exception,
and MCP only for a persistent service. For a generalist request or more than
ten tools, load tool details before planning. This skill does not authorize any
of those tools.

## Decision tree

1. Resume the same private task state when present. If no ledger exists, run a
   clearly labelled initial intake using known, sourced information and mark
   every unknown as `not_reported`.
2. At each configured checkpoint ask only for facts not already known. Track
   treatment, medication, supplements, diet, protein, hydration, exercise,
   sleep, energy, mood, stress, digestion, weight, waist, symptoms, and
   appointments when the consumer has enabled those fields.
3. Preserve the source, timestamp, confidence, attachment provenance, and
   correction history. Keep clinician-scale and home-scale measurements as
   separate series when both exist.
4. Calculate trends and prepare questions, but do not diagnose, change a dose,
   approve treatment, approve an unidentified supplement, or provide false
   reassurance. Mark such requests `requires_clinician_decision`.
5. Produce a private report only for the configured person and destination.
   The report may summarise trends and missing data, but it is not medical
   advice.

## Capacity boundary

The only cross-system value permitted by default is one coarse work-capacity
state: `high`, `normal`, `reduced`, `unavailable`, or `recovered`. It carries no
symptoms, medication, photos, measurements, or causal explanation. When the
state is `reduced`, the consumer workflow asks whether time off is needed and
for how long; if not, the time planner may reorganise toward easier work more
slowly. A capacity state never authorizes work or medical action.

## Storage and privacy

Detailed health records, photographs, medication, treatment, diet, exercise,
sleep, mood, and symptoms remain in the consumer's private encrypted store and
approved private backup. They are excluded from work digests, LiNKbrain,
shared telemetry payloads, and subordinate-agent messages. The library's
telemetry records only non-sensitive lifecycle metadata and the consumer's
explicitly permitted coarse outcome.

## Workflow and contracts

1. Checkpoint `INITIALIZED` and record the ledger version and privacy policy.
2. Ingest the initial intake or checkpoint and append observations/corrections.
3. Compute trends with explicit source labels and identify questions or risks.
4. Emit the permitted capacity state separately from the private report.
5. Export only through the consumer's encrypted backup authority.
6. Checkpoint `COMPLETED` only after ledger and report validation.

| Direction | Artifact | Schema |
| --- | --- | --- |
| Input | `health_request` | `./references/schemas.json#/definitions/input` |
| Output | `private_health_result` | `./references/schemas.json#/definitions/output` |
| State | `health_state` | `./references/schemas.json#/definitions/state` |

Read `references/api-specs.md` for the field and privacy contract and
`references/old-patterns.md` before changing a health workflow.
