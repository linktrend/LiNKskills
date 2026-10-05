# Worked synthetic success example — legal-lawve-agent-authority-charter-builder-arkadiy-miteiko

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `agent_identity`: Synthetic refund assistant v2; staging only; purpose is to draft refund recommendations.
- `principal_and_delegation`: No signed delegation supplied; product manager says refunds under $20 are allowed.
- `systems_and_data`: Read order records; can draft case notes; no payment write interface supplied.
- `action_inventory`: Read order, draft recommendation, approve refund, initiate payment, close case.
- `human_controls`: Finance owner not named; support lead can review draft; suspension route unknown.
- `evidence_requirements`: Case ID, source records, reviewer identity, approval timestamp, policy version.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/agent-authority-charter-builder-arkadiy-miteiko/SKILL.md

**Worked task output**
Draft action boundary: allow order lookup only after the read interface and case evidence are confirmed; drafting a refund recommendation is a proposal, not approval. Exclude refund approval, payment initiation and case closure because no signed delegation or payment-write interface is supplied. The product manager’s “under $20” statement is unverified. Charter fields still needing named owners: finance approver, policy version, review trigger and suspension route. No refund or case action is authorized.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
