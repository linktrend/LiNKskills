# Worked synthetic success example — legal-lawve-normalisation-juridique-christophe-quezel-ambrunaz

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `source_document`: Synthetic French contract DOCX text export, v1; original file hash is supplied separately.
- `language_and_locale`: French (France); English-defined terms appear in quotes.
- `editing_mode`: Propose safe typography and separately flag judgment edits; no native DOCX editor shown.
- `style_and_whitelist`: House style absent; preserve all defined terms and citations.
- `output_options`: Provide reversible change register and example corrections, do not claim file edited.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/normalisation-juridique-christophe-quezel-ambrunaz/SKILL.md

**Worked task output**
No edits are reported because the fixture describes a DOCX text export but provides no excerpt to normalize. Prepare a reversible change register with separate columns for deterministic typography and judgment edits; preserve citations, defined terms and quoted English expressions. Request the actual v1 text and house style. Since no native DOCX editor is shown, do not claim an edited or rendered file.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
