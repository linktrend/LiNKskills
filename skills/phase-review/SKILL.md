---
name: phase-review
description: "One phase-end review: Standards and Spec axes plus pre-landing bug hunt, and a PR body. Does not open or merge the PR."
usage_trigger: "Use once at phase end for the integrated diff. Do not review every issue. Do not open or merge pull requests."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [execution, review]
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

# Phase Review

Pin the fixed point (phase base). Confirm `git rev-parse` and a non-empty `git diff <base>...HEAD`.

## Axis A — Standards

Documented repo standards win. Always apply Fowler smells as judgement calls unless the repo endorses the smell: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest. Skip what tooling already enforces.

## Axis B — Spec

Against the phase briefs and PRD: missing or partial requirements; scope creep; wrong implementation. Quote the spec line.

Run the two axes as separate passes so one cannot mask the other. Do not merge rankings.

## Pre-landing bug hunt (gstack review)

Hunt bugs that pass CI: races, authz holes, missing rollback, broken empty states, leaked secrets. Auto-fix only obvious safe nits in this phase if the consumer allows; otherwise list them. Do not re-run Verification.

## PR body (do not open)

Write a body the packager can use: summary, test plan, risk, rollback. Shape: what changed, why, how to verify. Do not open, merge, or promote. GitHub integrate is not this skill.

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
