---
name: hr-interview-preparation
description: "Prepare structured interview plans and consistent competency-based scorecards for one role and interview loop."
usage_trigger: "Use when Sara is asked to design or prepare interview questions, panel assignments, scorecards, or a debrief for a specific role."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [human-resources, recruiting, interview-design, structured-interview]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 32000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, list_dir, get_tool_details, write_file]
dependencies: []
permissions: [fs_read, fs_write]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# HR Interview Preparation

## Role and outcome

Prepare an evidence-based interview kit for a defined role and hiring stage. The kit contains role-relevant competencies, a question bank, interviewer assignments, a behaviorally anchored 1–4 scorecard, and a structured debrief. Keep questions consistent across candidates for the same stage, while allowing neutral follow-up probes to clarify evidence. Do not infer a candidate's suitability from protected or irrelevant personal traits.

## Task workflow

1. **Intake:** confirm role, level, stage, approved job description/requirements, must-have vs trainable skills, interviewers and time budget. Identify what is known from dated company records versus founder/manager input. Ask only for missing facts that materially change the interview design; continue drafting unaffected portions.
2. **Competency map:** select 4–6 observable competencies linked to role outcomes. For each, write (a) the job requirement, (b) observable positive evidence, (c) evidence that is insufficient, and (d) the planned interviewer. Avoid redundant competencies and criteria that cannot be assessed in the interview.
3. **Question design:** for each competency create 2–3 behavioral questions and 1–2 situational questions; select a short core set that fits the time budget. Use open prompts about actions, constraints, result and learning. Add neutral probes such as “What was your part?” and “What changed because of your action?” Provide equivalent alternate prompts if a candidate has not encountered the exact scenario.
4. **Scorecard:** use a common 1–4 scale with behavior anchors specific to each competency: 1 = no relevant evidence / major gap; 2 = partial evidence with material support needed; 3 = meets the stated role bar with specific evidence; 4 = strong, repeated evidence beyond the stated bar. A score is not a hiring decision. Include evidence notes and “not assessed” when a question was skipped.
5. **Panel plan:** allocate each competency once where feasible; avoid asking every interviewer to cover everything. Include interviewer, competency, questions, time, handoff and note-taking instructions. Add a short opening, candidate questions and close.
6. **Debrief:** collect independent evidence and scores before group discussion. Discuss score differences by returning to observed evidence and the published role bar; do not average unsupported impressions. Record unresolved evidence gaps and the accountable hiring decision owner.
7. **Deliver:** return a ready-to-use interview kit, source list, assumptions, open decisions and brief change notes. Routine drafting does not require approval. Human owner makes hiring decisions and approves any change to the role bar.

## Evidence and fairness controls

- Cite job-description title/version/date and each approved requirement used. Label proposed competencies as proposed if the role definition is incomplete.
- Do not request or score age, disability/health, family status, religion, race, nationality, protected activity, or other personal characteristics unrelated to documented role requirements. If a candidate raises accommodation needs, route to the authorized HR process without recording unnecessary details here.
- Do not invent legally required interview questions, retention rules, or jurisdictional restrictions. If law affects the request, collect jurisdiction and current authoritative source; mark unresolved legal questions for counsel/HR.
- Candidate-specific comparisons are not part of this design task unless explicitly requested with authorized, minimized evidence and the relevant evaluation protocol.

## Native tools and persistence

The required tool names are contract labels only. For Sara, map `read_file` to native `read`; use a known approved path because no callable `list_dir` exists. Map `write_file` to native `write`/`edit` only for an explicitly requested interview-kit draft artifact. `get_tool_details` means inspect the current native tool schema and owner toolcard; it is not a callable alias. `linkbrain_read` may retrieve approved role facts in its available scope. Use `linkskills_use` only for already-qualified releases. If an approved read/write interface is unavailable, complete from supplied context and report the exact gap. Do not run shell scripts or write runtime sidecars; OpenClaw state remains SQLite-owned and checkpoints use the consumer owner interface.

## Contract

Input and output contracts are at `references/schemas.json#/definitions/input` and `/output`. Full active procedure: `advanced/advanced.md`. Immutable source and license are retained at `references/upstream/`.


## Execution profile and tooling levels

This is a Specialist workflow with a small, fixed native tool surface. The template names four CLI-first levels: Level 1 native CLI, Level 2 CLI wrapper, Level 3 direct API, and Level 4 MCP. These are routing categories, not available Lisa executors. Sara's current consumer has no shell/native CLI, no approved CLI wrapper, and no callable direct API alias; do not invent commands. Use only current native tools whose schemas/toolcards are visible, including an expressly approved read-only MCP where its contract supports the exact operation. If no approved interface is available, work from supplied evidence and name the interface gap.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.


## Tooling Protocol (CLI-First)

- **Native CLI:** no skill-specific system command is required; use only the current supported artifact interfaces.
- **CLI wrapper:** do not create or invoke a wrapper for this workflow.
- **Direct API:** use only a currently supplied native schema and owner toolcard when a read or private draft write is required.
- **MCP:** use only an explicitly exposed, owner-approved read capability; source skill connector names do not establish availability.

These are template routing categories, not claims that a specific CLI, shell, API or MCP tool is available.

- Task-specific source documents and blank/filled examples: `references/library/INDEX.md`.
