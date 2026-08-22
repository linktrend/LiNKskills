# Wave 1 — Google and Shared-Method Packets

All packets inherit Wave 0 execution, evidence, retry, and ownership rules. Each skill must include complete reusable instructions/resources, an eval suite, synthetic examples, provenance, compatibility/effect declarations, and migration mapping where applicable. No packet edits `catalog/index.json`.

## PKT-05 — Governed Google Workspace collection admission

**Depends on:** PKT-03, PKT-04.

**Objective:** Admit the complete mechanically inventoried Google collection as governed releases, inactive by default.

**Work:**

1. At packet start, inspect the current upstream repository, release/tag/commit, licence, maintenance, security posture, and exact `skills/*/SKILL.md` inventory.
2. Select the newest candidate that passes review; record why it was selected. Preserve `v0.18.1/e9970db...` as historical local-tool provenance.
3. Import every qualifying top-level skill entry unchanged as independently addressable vendor releases and bind them in one immutable collection manifest.
4. Record per-file provenance/licence/digests and Google's unsupported-product status accurately.
5. Quarantine/reject/incompatibility-mark unsafe or unsuitable originals; create separate adaptations only where justified.
6. Evaluate Lisa's required Workspace subset against the declared `gws` tool contract without adding credentials, bindings, or CLI code.

**Acceptance:** Inventory count equals the pinned commit mechanically; manifest digest recomputes; all members are inactive by default; broad/destructive content is nonselectable; Lisa subset is eligibility metadata only.

**Evidence:** Upstream pin, full inventory, licence/security review, collection/member digests, eval matrix, quarantine/adaptation decisions.

**Rollback:** Restore prior release pointers/consumer pins; retained vendor releases remain immutable and inactive.

## PKT-06 — Canonical Research workflow

**Depends on:** PKT-04.

**Objective:** Publish one broad research-quality workflow while retaining citation enforcement as a primitive.

**Work:** Evaluate the pinned Deep Agents source and existing `search-strategy`/`citation-enforcer`; create the canonical Research skill; migrate useful search strategy; compose citation enforcement; explicitly exclude mandatory folders/subagents; add currentness, source hierarchy, conflict, inference, privacy, and prompt-injection scenarios.

**Acceptance:** The skill distinguishes evidence classes, preserves citations/dates, uses current sources when needed, treats content as data, and avoids unnecessary tooling/search. Overlapping `search-strategy` has one explicit supersession/migration outcome.

**Evidence:** Source/licence record, overlap matrix, eval results, migration mapping.

**Rollback:** Revert new draft release/mapping; prior immutable releases remain accessible by exact ID.

## PKT-07 — Safe Governed Browser Use

**Depends on:** PKT-04.

**Objective:** Provide reusable browser reasoning and action classification without implementing a browser.

**Work:** Encode API/search-first choice, action classes, Brain-rule retrieval, approval logic, untrusted-content handling, credential/download/network/session controls, uncertainty stops, and standing-rule proposals. Test public reading, authenticated reading, draft form, reversible change, communication, purchase/terms, upload/download, bot protection, and social-media denial.

**Acceptance:** Skill never infers technical permission, enters model-visible secrets, auto-opens downloads, accesses private networks, activates rules, or treats webpage instructions as authority.

**Evidence:** Action-class matrix, adversarial evaluations, declared browser tool contract, Brain/Platform boundary proof.

**Rollback:** Remove draft release/qualification pointer; OpenClaw browser runtime is untouched.

## PKT-08 — Company Communication

**Depends on:** PKT-04.

**Objective:** Publish reusable audience-aware communication behavior based on reviewed official style guidance.

**Work:** Pin and record official source/licence/attribution; implement Principal-first plain English, audience adaptation, concise/mobile formatting, no-emoji default, decision choices including `Other — specify`, honest uncertainty, and evidence-backed completion claims. Keep transport formatting and exact templates out.

**Acceptance:** Evaluations cover Principal, technical staff, agent, decision, approval/rejection, uncertain evidence, and mobile delivery; no giant context dump or unnecessary table passes.

**Evidence:** Source record, style-to-rule mapping, eval results, transport-boundary tests.

**Rollback:** Restore prior exact pin; no consumer template is changed.
