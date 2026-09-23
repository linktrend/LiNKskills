---
name: ship
description: "Package the Verification tree: version, changelog, and release commit without a second full test when Verification already passed."
usage_trigger: "Use at Shipment after the tree is proven identical to the Verification result. Do not re-run the full Verification suite on an unchanged tree."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [shipment, release]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, shell_exec, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write, shell_exec]
scope_out: ["Do not claim live or usable certification", "Do not print secrets", "Do not weaken consumer delivery gates"]
format_profile: simple
last_updated: 2026-09-22
---

# Ship

Packages the tree Verification already passed. Automate routine work. Stop for blockers.

## Pre-flight

1. Confirm `HEAD` matches the Verification proof identity (commit or tree hash in the proof manifest). If it does not match, **stop** — this is not Shipment.
2. Detect platform and base branch from `git remote` / `gh` / `glab` / git-native fallback. Print the base branch.
3. You must not be on the unprotected guess of production. Work the release branch the plan names.
4. Do **not** re-run the full test suite, coverage gate, or adversarial re-review when step 1 passed. Those were Verification. If the tree changed, return to Verification.

## Version and changelog

- Auto-pick MICRO/PATCH when the plan does not name MAJOR. Stop and ask only for MINOR/MAJOR when the PRD said breaking.
- Update VERSION and CHANGELOG from the diff against the Verification base. Do not invent features.

## Commit

- Bisectable commits if the consumer requires them; otherwise one release commit is allowed when the plan says so.
- Never commit secrets. Run the consumer git safeguard.
- Push the work branch. **Do not open a pull request** unless the consumer plan explicitly says this skill opens one. LiNKdeveloper packager opens the Phase PR. gstack's "open a PR" step is then: write the PR body to the proof folder for the packager.

Idempotent: re-running means run the checklist again, not duplicate bumps.

## Tooling protocol (CLI-first)

1. **Native CLI** for git, files, screenshots, tests, and local inspection.
2. **CLI wrapper** scripts under this skill's `scripts/` for deterministic checks.
3. **Direct API** only when the consumer already authorized that exact service and a CLI cannot do the work.
4. **MCP** only for an approved persistent adapter.

When the task is generalist or exposes more than ten tools, call `get_tool_details` and cache only the selected schemas.

## Contracts

Validate input against `references/schemas.json#/definitions/input`.
Emit output against `references/schemas.json#/definitions/output`.
Append `{timestamp, skill, status, summary}` to `execution_ledger.jsonl`.
Never print secrets, tokens, or private credentials.

This skill is draft catalog procedure. It does not grant permission-to-act, does not mark itself live or usable, and cannot weaken the consumer's proof, review, integration, promotion, or named-server deploy gates.
