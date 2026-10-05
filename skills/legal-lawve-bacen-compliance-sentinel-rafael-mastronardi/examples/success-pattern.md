# Worked synthetic success example — legal-lawve-bacen-compliance-sentinel-rafael-mastronardi

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `institution_and_activities`: Synthetic fintech says it is a payment institution in Brazil; license/supervisory status not supplied.
- `regulatory_topics`: Cloud outsourcing and Open Finance consent review.
- `control_evidence`: Vendor contract mentions encryption; no exit plan, audit right or consent log supplied.
- `service_and_data_flow`: Cloud region in US; customer transaction data may be processed; exact criticality unknown.
- `current_authority_refs`: No official BCB/CMN text attached.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/bacen-compliance-sentinel-rafael-mastronardi/SKILL.md

**Worked task output**
Conditional issue register: self-description as a payment institution is not evidence of BCB supervision. Topics: cloud outsourcing and Open Finance consent. Evidence gaps: license/supervisory status; current BCB/CMN text; cloud exit and audit rights; data criticality/US processing map; consent logs. Record encryption mention as a supplied contract statement only, not verified control operation. No regulator notification or control change.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
