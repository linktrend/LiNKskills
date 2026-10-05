---
name: legal-commercial-nda-review
description: "Review a commercial NDA against supplied deal facts, governing-law text, and company-approved negotiation positions; prepare clause analysis, proposed edits, and counsel-ready issues."
usage_trigger: "Use when Sara is asked to review, triage, analyze, or prepare proposed redlines for an inbound or outbound commercial NDA."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, commercial-contracts, nda, clause-review, draft-redline]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 64000
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
# Commercial NDA Review

## Role and outcome

Produce substantive, evidence-based draft analysis of a commercial NDA: identify the parties and direction of disclosure, summarize obligations, compare terms to the supplied approved playbook, assess stated legal and business risks, and prepare proposed clause edits or negotiation alternatives. Every conclusion is a reviewable draft with source text, section/page reference, date, governing-law facts and stated uncertainty. Sara may prepare analysis and language within the task; Carlos or external counsel reviews consequential legal conclusions and final terms. No document is signed, sent, submitted, or changed in a system by this skill.

## Intake and scope

1. Read the complete agreement and amendments supplied for this task; identify version/date, parties, transaction context, company role (discloser, recipient, mutual), intended data sharing and decision deadline.
2. Identify the express governing law, venue and dispute forum from the actual text. If absent, conflicting, foreign, or unclear, say so. Never substitute a default jurisdiction or imported law.
3. Read the applicable company-approved clause playbook if provided, recording title/version/date and owner. If none exists, perform neutral issue analysis and offer alternatives; do not label terms “standard,” assign a green light, or invent company positions.
4. Determine whether the document is actually limited to confidentiality. Flag and separately analyze standstill, exclusivity, non-solicit/non-compete, IP license or assignment, ROFR/MFN, broad release, arbitration, data protection, security, service, purchase or investment terms. Recommend separate review where they materially change scope; continue the rest of the analysis.
5. Clarify the intended task only when missing party-side or deal facts would materially change analysis. Otherwise mark the uncertainty and proceed with separable clauses.

## Clause-by-clause analysis

For each operative clause, record: section/page; concise source quote or faithful summary; obligation and who bears it; duration/scope; interaction with defined terms and other clauses; playbook match (supported / deviates / silent); factual assumption; risk rationale tied to text and supplied authority; business friction; and proposed disposition.

Check at minimum:

- Definition and marking of confidential information, oral disclosures, exclusions, and compelled disclosure process.
- Permitted purpose, permitted recipients/representatives, affiliate/contractor access, responsibility for recipients, and onward disclosure.
- Standard of care and security obligations; whether they impose measurable, operationally possible duties.
- Term, survival, trade-secret treatment, and whether commencement/end dates are clear.
- Return/destruction, legal retention, routine backups, archival copies, and certification obligations.
- Residual knowledge, independent development, third-party disclosures, and prior knowledge.
- Remedies, injunction language, damages limits, indemnity, fee shifting, and any waiver language.
- Governing law, venue, arbitration, notice mechanics, assignment, successors and order of precedence.
- Hidden commercial restraints or rights beyond confidentiality.

Do not state enforceability unless you have identified the actual jurisdiction, current authoritative legal source and relevant facts; frame uncertain conclusions as issues for counsel. Compare contract text and playbook independently: a playbook mismatch is a business-position variance, not itself a legal violation.

## Draft redlines and alternatives

When requested or useful, draft precise, clause-level redline language. Prefer a surgical edit that preserves unaffected text. For each edit provide (1) proposed language, (2) the protection or commercial objective it addresses, (3) a reasonable fallback, and (4) trade-off if accepted. Preserve defined terms and cross-references; mark missing facts with brackets rather than guessing. Do not represent draft language as agreed, final, or legally sufficient.

## Output

Return: executive issue summary; agreement facts; governing-law/source scope; clause table; proposed redlines and fallback options; factual/legal gaps; questions for business owner; counsel review points; and next action owner. Use `NEEDS_CONTEXT` only for fact-dependent parts; complete unaffected analysis. The status is a draft-review status (issues found / no material issues found under supplied criteria / incomplete), never “approved,” “safe to sign,” or a signature authorization.

## Authority and action boundary

Substantive legal research, contract interpretation and drafting are allowed as draft work grounded in identified sources. The boundary is final authority and external effect: do not sign, accept, send, file, upload to CLM, promise terms to a counterparty, or declare company approval. Refer consequential conclusions, unusual risk allocation, jurisdiction-sensitive enforceability, and final language to Carlos or external counsel. Do not escalate every ordinary clause; identify the specific question and evidence needing review.

## Native tools and persistence

The required tool names are contract labels only. Map `read_file` to native `read`; use a known approved path because no callable `list_dir` exists. Map `write_file` to native `write`/`edit` only for an explicitly requested internal draft. `get_tool_details` means inspect the current native tool schema and owner toolcard; it is not a callable alias. Use supplied documents first and only approved read-only Odoo/MCP surfaces when the current native schema supports that exact lookup. If no approved interface exists, report the gap instead of inventing a call. No shell scripts, legal-system writes or runtime sidecars; OpenClaw state remains SQLite-owned and checkpoints use the consumer owner interface.

## Contract

Input and output contracts are at `references/schemas.json#/definitions/input` and `/output`. Detailed review cards are in `advanced/advanced.md`. Immutable source and license are retained at `references/upstream/`.


## Execution profile and tooling levels

This is a Specialist workflow with a small, fixed native tool surface. The template names four CLI-first levels: Level 1 native CLI, Level 2 CLI wrapper, Level 3 direct API, and Level 4 MCP. These are routing categories, not available Lisa executors. Sara's current consumer has no shell/native CLI, no approved CLI wrapper, and no callable direct API alias; do not invent commands. Use only current native tools whose schemas/toolcards are visible, including an expressly approved read-only MCP where its contract supports the exact operation. If no approved interface is available, work from supplied evidence and name the interface gap.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

- Task-specific source documents and blank/filled examples: `references/library/INDEX.md`.
