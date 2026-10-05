# Worked synthetic success example — legal-lawve-icelandic-privacy-review-magnus-smarason

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `processing_description`: Synthetic Iceland clinic intake uses kennitala, appointment details and optional health notes.
- `controller_processor_roles`: Clinic decides purpose; cloud vendor hosts records; processor terms not supplied.
- `document_and_controls`: Notice says data retained “as needed”; no retention schedule or DSAR workflow supplied.
- `iceland_connection`: Clinic established in Iceland; patient location varies.
- `authority_snapshot`: No current Icelandic regulator/primary source attached.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/icelandic-privacy-review-magnus-smarason/SKILL.md

**Worked task output**
Processing map: Iceland clinic decides purpose (controller fact supplied); cloud vendor hosts records (processor terms absent). Intake includes kennitala, appointment details and optional health notes; minimize these fields pending purpose/necessity review. “As needed” retention is not an operational schedule; DSAR workflow is absent. Separate Icelandic and EU authority checks, verify current sources, and request retention, vendor terms and rights workflow. No current compliance conclusion.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
