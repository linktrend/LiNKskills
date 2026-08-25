---
name: personal-compliance
description: "Configurable selfie-compliance state transitions and privacy-preserving adaptive battery preparation with uncertainty-aware image correction."
usage_trigger: "Use when a consumer-owned private workflow needs a reusable selfie window, battery estimate, bundled measurement, or image-extraction correction plan without storing personal data or sending reminders."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-24
author: LiNKskills Library
tags: [personal-compliance, selfie, battery, privacy, state-machine]
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
dependencies: [company-communication]
permissions: [fs_read, fs_write]
scope_out: ["Do not store or transmit real selfies, battery values, locations, routines, schedules, identifiers, health details, or credentials", "Do not own a private ledger, calendar, reminder transport, image store, device connector, charger binding, or consumer profile", "Do not diagnose, change treatment, infer consent, send reminders, or activate standing rules", "Do not copy Lisa canary schedules, thresholds, locations, rates, destinations, or other private bindings into this generic release"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-08-24
---

# Personal Compliance

This skill is a reusable reasoning contract for two configurable workflows:
selfie compliance and adaptive battery tracking. It prepares a typed result for a
consumer-owned private ledger or adapter; it never owns that ledger or invokes a
calendar, reminder, image, device, health, or messaging system.

## Decision tree

1. Resume only the matching synthetic task identity and validate the input
   contract. Reject restricted data, real images, credentials, identifiers, and
   missing provenance before reasoning.
2. Load the consumer-supplied configuration. The generic release has no default
   personal window, threshold, charger, location, rate, routine, destination, or
   reminder time.
3. Classify the requested mode as `selfie_compliance`, `battery_tracking`, or
   `combined`. Keep confirmed, inferred, not-reported, and unknown values distinct.
4. Apply the selfie state machine: `EARLY`, `COMPLETED`, `REPORTED_LATE`, or
   `MISSED`. Conditional reminders are only proposed; existing reminder references
   suppress duplicates and no transport is called.
5. Learn charger/location-specific rates only from valid synthetic observations.
   Calculate discharge and saturation-aware charge estimates, then project the
   configured alert threshold (including a configured 35% projection policy)
   before the next expected charge. An hourly check
   with no material alert is silent, and a maintenance alert never cancels
   maintenance.
6. Bundle configured measurements once per checkpoint. A final checkpoint closes
   the day and does not request another reading.
7. For image extraction, return only material values and uncertainty. Confirm only
   material ambiguity; corrections append history and never silently overwrite the
   confirmed value.
8. Validate output, effects, evidence, idempotency, and the exact rollback pointer.
   Any reminder, external call, diagnosis, treatment change, or private-state write
   remains owned and gated by the consumer. Missing evidence returns
   `PENDING_APPROVAL` rather than guessed completion.

## Selfie state machine and reminders

The caller supplies a valid window and capture/completion evidence. A capture before
the window is `EARLY`; one inside is `COMPLETED`; one after the close is
`REPORTED_LATE`; no report after the window closes is `MISSED`. A reminder is a
proposal with a reason and owner, never a sent message. When a matching reminder
reference already exists, the proposal is suppressed as a duplicate. Completion
also suppresses all conditional reminders.

## Adaptive battery reasoning

Observations must be synthetic, typed, and timestamped. Charge and discharge rates
are learned separately for a supplied charger/location context, with enough valid
observations to avoid guessing. Charging estimates slow as the configured upper
target is approached (saturation); discharge projections use the supplied next
charge horizon. The result reports the recorded value, rate label, projected value,
configured threshold, and whether a material alert is required. No device read,
location lookup, notification, or maintenance cancellation occurs here.

## Privacy, uncertainty, and authority

Detailed private state stays in the consumer-owned private ledger. Releases,
fixtures, evals, telemetry, Brain records, and subordinate outputs contain only
synthetic references and redacted digests. Unknown or not-reported evidence is
preserved and escalated rather than guessed. This skill does not diagnose, change
treatment, infer a health conclusion, or provide emergency wording. Images are
referenced by opaque synthetic IDs only; image bytes never enter the workflow.

## Tooling and contracts

Use the native CLI for local evidence, then a consumer-supplied CLI wrapper. A
direct api and MCP are exception-only adapter paths. A specialist is preferred
for privacy or authority ambiguity; a generalist may only normalize complete
evidence. Call `get_tool_details` for a generalist or multi-tool run. The offline
helper has no network or device imports.
Input, output, and state contracts are in
[`references/schemas.json#/definitions/input`](references/schemas.json),
[`references/schemas.json#/definitions/output`](references/schemas.json), and
[`references/schemas.json#/definitions/state`](references/schemas.json). Read the
eval suite, advanced guidance, examples, and old-patterns before qualification.

Every result is idempotent, effect-free, evidence-bound, and rollback-addressable.
OpenClaw owns schedules, profile bindings, private SQLite state, destinations, and
delivery. Platform owns identity and capabilities. LiNKskills owns only this
generic reasoning contract and its tests.
