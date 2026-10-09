# LiNKskills — Business handover

Assessment: **9 October 2026, Asia/Taipei**. Live inspection: approximately **19:45–19:47 Taipei**. Prepared for a new business AI agent and the Principal, Carlos. Read this report together with [the engineering handover](LINKSKILLS-ENGINEERING-HANDOVER-2026-10-09.md). This is a dated assessment, not a new PRD or permission to change production.

## Purpose and receiving workflow

LiNKskills is LiNKtrend’s internal library of reusable AI procedures. Agents find a skill, retrieve the approved version and the supporting material they need, perform the work under their own Program’s permissions, and report use or problems. Authors and the Librarian use evaluation results and feedback to improve the library. Success means the agreed agents can reliably find and use the right approved procedures, while unsuitable versions are withheld and problems can be traced and corrected.

**LiNKskills is deployed to LiNKserver 01.** The running service was freshly observed healthy with successful health and readiness responses. This establishes an operating service and a reachable store. It does not establish that every skill, consumer, or scheduled process works end to end.

The business agent receives both reports, discusses the unresolved decisions below with the Principal, and supplements this business report. It then forwards the supplemented business report and the **unchanged engineering report** to an engineering agent. That agent prepares the actionable technical PRD and delivery plan. Neither report authorizes rebuilding working components.

## Users, workflows, and boundaries

The Principal is the sole human decision-maker. The primary users are internal AI agents, especially OpenClaw Prime’s Lisa, Eric, Sara, David, and Jane. Skill authors and the institutional Librarian maintain the library. Codex, Cursor, and AI-agent-based LiNKautowork automations are also requested consumers, subject to the additional effort condition recorded below. There is no confirmed requirement for a public customer product or a new user interface.

| Workflow | Input | Expected output and boundary |
|---|---|---|
| Discover and retrieve | Agent identity, task, skill/release reference | Catalog descriptions and exact approved instructions/resources; load only the material needed. |
| Use a skill | Retrieved procedure, consumer’s tools and own permissions | Work performed by the consumer. The library does not itself grant authority to act. |
| Report use or feedback | Bounded outcome, release reference, safe evidence reference | Durable acknowledgement/status; no raw private conversations or business records in library telemetry. |
| Author and qualify | Versioned skill source and executable evaluation cases | Tested candidate and evidence of suitability for its intended execution context. Merely having a document is insufficient. |
| Publish or withdraw | Accepted candidate and authorized publication action | Immutable release or lifecycle change. Published bytes must not be overwritten. |
| Librarian curation | Redacted feedback, evaluation evidence, candidate changes | Improvements and escalation decisions through the assigned host and release process. |

LiNKplatform owns identities, authentication, capability grants, and shared database administration. Each Program owns permission to act and its operational ledger. LiNKbrain is a separate knowledge and memory service. LiNKskills must preserve these boundaries, the existing production data, approved releases, working agent integrations, and the temporary checkout-loading compatibility route where still needed.

## What works and what the evidence means

| Finding | Evidence strength | Limit |
|---|---|---|
| Service is deployed and running on Server01 | Fresh read-only container inspection and HTTP 200 health/readiness on 9 October | No new authenticated consumer workflow was performed. |
| Initial publication, authenticated retrieval, use/feedback receipts, duplicate replay/conflict handling, restart, backup restore, and rollback were demonstrated | Original 15 September acceptance receipt re-read and its checksum verified | Covered five initial releases and a private consumer binding on that older deployment. Its “12/12” completion was bounded to that release; it is not proof of today’s complete application scope. |
| Native skill retrieval by Sara and Eric has worked | Dated 4 October operator receipts: Sara 34 successful checks across her main context and five specialist contexts; Eric retrieved five planning skills | Retrieval and reported qualification status do not prove substantive business execution or independent semantic quality. |
| Core provider and deployment-candidate behavior has passing local tests | 21 tests passed on the current protected source tree during this assessment | Local tests do not establish current production behavior. |
| Jane has an enabled provider binding in a prior record | Scoped 5 October administrative readback records 291 allowed release IDs | Administrative metadata does not prove Jane’s caller permissions, specialist mapping, or the quality of those releases. |

Supporting evidence and checksums are retained in the engineering report. The [initial release contract](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/docs/archive/handoffs/2026-09-15-successor-release.md) explains the original boundaries.

## Incomplete, defective, and unverified areas

**Verified inconsistency:** production is running a mixture that cannot currently be identified by one protected repository version. Image labels name the older 1.0 source, two inspected installed modules differ from protected source, and the live catalog has 85 entries while current protected source has 348. Existing working service behavior should be preserved while engineering and the server owner explain and reconcile this. These counts represent catalog entries, not counts of independently qualified skills.

**Verified source catalog inconsistency:** the generated source index failed its own provenance check, and all 348 source cards are marked draft. This requires reconciliation with actual published releases; it does not mean the 348 entries are broken.

**Verified documentation/metadata drift:** repository guides still describe older releases and counts. Runtime readiness reports the older API contract version while deployment labels name the newer contract. This reporting discrepancy needs explanation; it does not by itself prove an API failure.

**Unverified:** completion of qualification and publication for the originally requested remaining 54 skills; the current accepted release inventory; authenticated behavior for all five OpenClaw agents and their relevant specialist contexts; Codex, Cursor and LiNKautowork adoption; current receipt persistence and isolation; current backup/restore and rollback readiness; and continuous monitored Librarian operation. No conventionally named Librarian container or system service was found, but other scheduling arrangements were not exhaustively inspected.

**Existing unfinished source work:** resource-loading improvements are integrated in protected source; separate quarantine and native-evaluation candidates remain outside that protected tree. Their presence cannot be counted as production completion. The engineering report identifies these candidates and their owners. There is no evidence here that replacement of the functioning application is necessary.

## Additional requirements already confirmed by the Principal

These statements come from direct instructions in this task’s prior conversation and remain the starting requirements; receiving agents must ask about changes rather than silently weaken them.

1. Qualify and publish **all of the original remaining 54 skills**, completing the original 59-skill release scope. The later larger catalog is a separate inventory reconciliation, not automatic expansion of this accepted denominator.
2. Ensure LiNKskills works with LiNKplatform and **all five OpenClaw Prime agents**. Platform identities and Server01 identity work were reported completed by the Principal; present usability still needs evidence.
3. Add **Codex, Cursor, and LiNKautowork automations that use an AI agent**, if possible without too much additional work. These were conditionally requested, not approved with an unlimited effort budget. The Principal later emphasized total LiNKskills completion rather than only avoiding OpenClaw delay.
4. Include **production Librarian scheduling**. A schedule, escalation route, and evidence of safe continuing operation must be agreed and demonstrated.
5. Keep the repository understandable: archive superseded development material, maintain the READMEs and AI-agent guide, identify LiNKskills 1.0, and retain only development/staging/main as long-lived branches after accepted delivery. Temporary and unfinished work must be assessed before removal. No cleanup is performed by this reporting task.
6. Engineering completes development, CI, release packaging, and a deployment-ready handoff; the **dedicated Server01 owner** performs deployment and final operational verification. GitHub must contain the technical material another IDE agent needs, with authorized access supplied separately.

Earlier blanket approvals and Founder Bootstrap requests were issued for earlier execution. They are historical decisions, not a waiver for this reporting task, future changes, spending, or publication protections.

## Decisions for the Principal and business agent

| Unresolved decision | Why it matters |
|---|---|
| After the original 59, which of the 348 source entries and later role-specific candidates must be included in final acceptance? | Source inventory growth cannot automatically become a requirement to qualify everything. Preserve the original 54 commitment and define the added scope explicitly. |
| What effort/cost limit makes Codex, Cursor and Autowork adoption “not too much work”? Which hosts and automation types count? | Determines whether conditional integrations can be accepted, deferred, or funded. No numeric budget was agreed here. |
| Should retained specialist contexts share their parent’s identity/binding or use separately registered identities? | Requires consumer-owner intent and Platform validation; native session IDs do not answer it. |
| What Librarian schedule, automatic-change limits, escalation response, and observation period count as ongoing operation? | Scheduling is confirmed; suggested times in older contracts are not an agreed operational policy. |
| What response time, availability, retention, and recovery targets should acceptance use? | The readiness request took about 15 seconds in one observation; no approved service target or recurring failure was established. |

No essential question needs to block these reports: the confirmed requests are stated precisely and the remaining choices are explicitly unresolved. These choices must be settled before the receiving engineering agent treats them as implementation requirements.

## Owners and practical completion checklist

**LiNKskills engineering** owns skill source, evaluation, publication code, Gateway/MCP, receipt behavior, domain Librarian, tests, documentation, and release packaging. **LiNKplatform Completion** owns authoritative identities/grants, credential lifecycle, shared migrations and generic Librarian hosting. **OpenClaw Prime and other consumer owners** own their agent configuration and tool authority. **Server01 Production Owner**, Codex task `01a0a309-7dfd-7a52-8764-2ebd7fa25be4`, owns installation, service operation, backups, rollback and production acceptance. The Principal approves unresolved product choices and protected release gates.

- [ ] Agree the final inventory, conditional consumer effort limit, specialist identity design, and Librarian operating policy.
- [ ] Establish the exact installed source/configuration and preserve a recoverable working baseline.
- [ ] Reconcile each agreed skill’s source, qualification, immutable publication, consumer binding and observed use; repair demonstrated gaps.
- [ ] Demonstrate discovery, exact retrieval and permitted use for each agreed consumer; prove denied access and safe error behavior.
- [ ] Demonstrate durable use/feedback acknowledgement, retry behavior and privacy preservation on the accepted deployment.
- [ ] Demonstrate supervised Librarian behavior, scheduled runs, monitoring, escalation and recovery before calling it continuously operational.
- [ ] Deliver protected source, signed artifact identity, migration/configuration manifest, acceptance commands and rollback packet to Server01.
- [ ] Have the server owner verify deployment, restart persistence and recovery, then record the Principal’s acceptance against the agreed criteria.

## Nonbinding recommendations

Retain the working production service while reconciling its installed bytes with source. Use a single current acceptance register listing each skill, profile, consumer and evidence rather than relying on catalog counts or repeated “100%” declarations. Choose small representative workflow checks first, then extend coverage to the agreed inventory. These are recommendations, not additional approved requirements.

## Assessment and delivery limitations

Investigation used the available Luna 6 model `gpt-6-luna` at high reasoning because “Luna 6 High” was not listed under that exact name. The parent agent synthesized the reports. This task did not fix code, change production data, deploy, run model calls, submit receipts, or activate schedules. Health/readiness and metadata were inspected; historical receipts were read rather than rerun. Independent report review and document-reference/secret checks are recorded in the delivery evidence for issue [#423](https://github.com/linktrend/LiNKskills/issues/423). Main publication is subject to the existing protected review/promotion process; these reports make no claim that a documentation checkpoint is already published on main.
