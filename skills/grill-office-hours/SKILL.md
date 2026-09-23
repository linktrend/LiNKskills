---
name: grill-office-hours
description: "Force a conversation before code: design-tree interview, domain glossary and ADRs in-repo, and office-hours premise challenge with a design doc."
usage_trigger: "Use at Intake elicitation before any code, when an idea, plan, or design must be sharpened and written down."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [intake, elicitation, interview]
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

# Grill Office Hours

No code. Write artifacts in the working directory. Do not use a no-directory interview.

## 1. Design-tree interview (Matt grilling)

Map the work as a **design tree**: every decision branches into the decisions that hang off it. The **frontier** is every decision whose prerequisites are settled. Ask the whole frontier in one round. Number each question. Give your recommended answer. Wait for answers before the next round.

Format:

```
Q1 — <title>: <body and choices>
Recommended: <answer>
```

Facts are your job: look them up; do not ask the user for filesystem or code facts. Decisions are the user's. The session ends when the frontier is empty. Do not act until they confirm shared understanding.

## 2. Domain model (Matt domain-modeling)

Challenge terms. Invent edge cases. Write them down when they crystallise.

- Create `CONTEXT.md` when the first term is resolved (or the mapped context file if `CONTEXT-MAP.md` exists).
- Create `docs/adr/` when the first architectural decision is needed. One ADR per decision: title, status, context, decision, consequences.
- Use the glossary vocabulary in later specs. Do not invent a second name for a settled term.

## 3. Office hours (gstack)

Ask the goal first, then pick a mode:

- Startup / internal product → **Startup mode**. Ask forcing questions **one at a time**. Push until answers are specific and evidence-based. Comfort is a signal you have not pushed enough.
- Hackathon, learning, open source, fun → **Builder mode**. Generate alternatives, pick a wild exemplar, then lock a small design.

**Six forcing questions** (startup; skip ones already answered; pre-product uses Q1–Q3; users Q2/Q4/Q5; paying Q4–Q6):

1. **Demand reality.** Strongest evidence someone would be upset if this disappeared tomorrow. Waitlists and "interesting" are not demand.
2. **Status quo.** What they do now, even badly, and what that workaround costs. "Nothing exists" usually means the pain is weak.
3. **Desperate specificity.** Name a person, title, and consequence. Categories are not people.
4. **Narrowest wedge.** Smallest version someone would pay for this week.
5. **Observation.** Watched someone use it without helping; what surprised you.
6. **Future-fit.** If the world is different in three years, does this become more essential? Growth rate is not a thesis.

Pushback: take a position on every answer and name what evidence would change it. Do not praise. After Q1, challenge undefined terms and hidden assumptions.

Write a design doc in-repo (prefer `docs/designs/` or `DESIGN.md`): problem, who, status quo, wedge, evidence, rejected alternatives, open questions. OpenClaw hosts use the same procedure.

If the user tries to skip twice, proceed only after recording the missing evidence as assumptions in the doc.

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
