# Worked synthetic success example — legal-lawve-employment-law-research-yue-deng-wu

**Task:** synthetic-golden from this skill’s `references/eval-suite.json`.

**Case facts**
- `topic_and_question`: Are pay-transparency postings required for a 22-person remote-first employer?
- `jurisdictions`: Federal plus California and New York City only; worker residence locations not supplied.
- `time_window`: Current through 2026-10-05; identify changes in previous 12 months.
- `facts_and_worker_groups`: Employer has 22 workers; role locations, employer entity and posting practices unknown.
- `source_policy`: Primary statute/regulation/official agency materials for rules; secondary sources clearly labeled.
- `scope_and_as_of`: Synthetic facts only; current law/applicability unverified unless explicitly supplied.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/employment-law-research-yue-deng-wu/SKILL.md

**Worked task output**
Research scope register: jurisdictions limited to federal, California and New York City; no 50-state survey. Employer has 22 workers, but entity, role locations, remote-worker residence and posting practices are missing. Build a three-jurisdiction table of current official statutes/regulations/agency guidance, effective date, employer/role coverage and posting requirement; mark each rule unresolved until primary text is retrieved. Separate enacted rules from bills/commentary and request worker-location facts.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
