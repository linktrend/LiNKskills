# Worked synthetic success example — legal-lawve-dpdpa-gdpr-compliance-review-parth-desai

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `document_text_and_type`: Synthetic SaaS DPA v3: processor may use data for service and analytics; no subprocessor list attached.
- `parties_and_roles`: India vendor and EU startup; contract labels parties controller/processor but actual purposes not established.
- `data_categories_and_people`: Account data and support tickets; children/sensitive data unknown.
- `processing_and_transfer_facts`: Hosting region and onward transfers unknown; analytics purpose stated.
- `authority_snapshot`: No current official Act/Rules or GDPR source attached.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/dpdpa-gdpr-compliance-review-parth-desai/SKILL.md

**Worked task output**
Role/scope worksheet: the DPA labels India vendor as processor and EU startup as controller, but actual purpose and role allocation are unverified. India and EU branches must be tested separately from entity, establishment, targeting and processing evidence. Findings limited to documents: analytics use is stated; subprocessor list, hosting region and onward-transfer facts are missing; sensitive/child data is unknown. Request these records and current Indian/EU primary authorities; draft clauses remain conditional and no regime conclusion is made.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
