# Worked synthetic success example — legal-lawve-hipaa-compliance-tanaji-hemant-naik

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `entity_and_role`: Synthetic analytics vendor receives lab records from a hospital; covered entity/BA status and agreement unknown.
- `workflow_and_data`: CSV contains patient name and lab result; storage and deletion facts incomplete.
- `systems_and_controls`: Cloud bucket access log is partial; risk analysis, MFA and backup evidence absent.
- `business_associate_docs`: No BAA attached.
- `official_authority_snapshot`: No current HHS authority attached.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/hipaa-compliance-tanaji-hemant-naik/SKILL.md

**Worked task output**
Scope/evidence map: vendor receives CSVs with patient names and lab results from a hospital, but covered-entity/business-associate roles are not established. BAA is absent; storage/deletion facts and full access logs are incomplete; risk analysis, MFA and backup evidence were not supplied. Request current HHS authority, role/relationship evidence, BAA and system/data-flow records. Do not declare HIPAA applicability, a breach or notification duty from the data type alone.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
