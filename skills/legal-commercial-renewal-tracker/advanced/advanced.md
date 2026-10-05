# Legal Commercial Renewal Tracker: task method

## Task trigger and finish condition

Extract each renewal, auto-renewal, notice, termination and price-change date from the operative contract set.

## Task-specific procedure

1. **Scope and intake.** Confirm the exact request, intended audience, deadline, matter/company identity, relevant approved policies, and requested output. Read the task-specific source inputs and active source method at `references/upstream/SOURCE-MANIFEST.json`; use source materials as methodology evidence, not as company facts or current law. The typed intake is `references/schemas.json#/definitions/input`.
2. **Build the evidence set.** Read supplied materials in full where feasible. Record document name/version/date, owner, location, and relevant page/section/row. Separate verified fact, source assertion, interpretation, assumption, and unknown. Preserve conflicting versions and contrary evidence.
3. **Apply this task method.** Extract each renewal, auto-renewal, notice, termination and price-change date from the operative contract set. Calculate dates only from explicit text and stated calendar assumptions, show the calculation, lead-time and time zone if supplied, and flag conflicts or missing notice mechanics. Return a proposed reminder schedule for an owner to enter; do not create reminders or send notices.
4. **Analyze and draft.** Produce the distinct deliverable: **renewal event table, source clause, date calculation, notice window, responsible owner if supplied, draft reminder timeline and uncertainty flags.** Use clear, reviewable sections; include source pinpoint, date/as-of basis, calculations where applicable, confidence limits and alternatives. For legal work, state the actual jurisdiction(s) and current primary legal authority/date used; if authority cannot be verified through an approved interface, label the legal point unverified and formulate a precise counsel research question. Never import foreign law as general law.
5. **Quality check.** Reconcile each material statement to evidence. Check completeness, internal consistency, dates/units, contrary facts, data minimization and every task-specific required output. Do not claim system status, approval, filing, signature, notice or completion absent direct evidence.
6. **Deliver.** Return the typed output plus a concise owner-ready summary. Draft language is allowed within this task; binding authority, execution, external sending/filing, commitments, personnel decisions and record changes remain with authorized humans. Consequential legal conclusion/action is for Carlos or external counsel review; routine reversible draft work need not wait for review.

## Source-specific method checkpoints retained

The following checkpoints come from the selected task's actual pinned entrypoint at `commercial-legal/skills/renewal-tracker/SKILL.md`. They are adapted as evidence/review topics in this card; source connector names, local paths, command invocations, hidden profile defaults, privilege assertions, current-law claims, and automatic external actions are not carried over. Use the currently available native consumer interfaces and the actual matter/company evidence.

- /renewal-tracker
- The register
- Business-day check on every cancel-by date
- Modes
- Mode 1: Ingest a renewal (handoff from review)
- Mode 2: What's coming up
- Renewals — next 90 days
- 🔴 Cancel-by deadline in 0–13 days
- 🟠 Cancel-by deadline in 14–44 days
- 🟡 Cancel-by deadline in 45–89 days
- Mode 3: Scan the [CLM] / e-signature tool to populate the register
- Mode 4: Missed windows (the bad news report)
- Missed cancellation windows
- Gate: accepting or declining a renewal
- Integration: renewal-watcher agent
- What this skill does not do

For each relevant checkpoint, record evidence or mark it not supplied/not applicable. The active task procedure above controls how to act; this list preserves the source task's distinct workflow coverage without importing unsupported runtime behavior.

## Native OpenClaw consumer mapping

- The aliases `read_file`, `write_file`, `get_tool_details`, `list_dir`, `linkskills_use`, and `linkbrain_read` are contract labels, not guaranteed callable native tools. Map `read_file` to the current native `read` tool on known approved paths. Map `write_file` to native `write`/`edit` only for a user-requested internal draft artifact. There is no callable `list_dir` alias. `get_tool_details` means inspect the currently visible native tool schema and owner toolcard; do not invoke an invented alias.
- Use `linkskills_use` or `linkbrain_read` only when present in the current live tool schema and the exact requested item is within its read scope. Named Odoo/MCP interfaces are read-only and usable only if the visible current native contract supports the exact query. Otherwise state the missing interface and continue from supplied evidence.
- Never use shell, scripts, APIs or guessed tool names for business systems. Do not mutate HR/legal/finance/vendor systems, send messages, file documents, make commitments, execute agreements, or store runtime state in files. OpenClaw runtime state remains SQLite-owned; checkpoints must use the supported consumer-owner interface if available.

## Boundaries and applicability

This is a substantive specialist drafting and analysis workflow, not a final approval authority. Do not invent company facts, legal rules, jurisdiction, client relationship, policy, approval, or records. Identify applicability limitations and as-of date. Preserve personal/confidential data only to the authorized scope; minimize sensitive personal, employment, health and privileged information. Mark attorney-client privilege only when counsel has directed and the factual/legal basis is documented.

## Task-specific acceptance

- Deliver the task-specific work product and evidence trace, not a generic departmental overview.
- Record assumptions, missing items, contradictory evidence, owner decisions, jurisdiction/source freshness and proposed next steps.
- Keep external effects and system mutations empty.
- If an interface is unavailable, report the exact capability gap without fabricating an invocation.
