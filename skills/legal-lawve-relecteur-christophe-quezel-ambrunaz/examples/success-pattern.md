# Worked synthetic success example — legal-lawve-relecteur-christophe-quezel-ambrunaz

**Task:** synthetic-golden from this skill’s `references/eval-suite.json`.

**Case facts**
- `document_text_or_ref`: Synthetic sentence: “Les partie signataire s’engage à transmettre leurs document.” Defined term “Service Level Agreement” must remain unchanged.
- `audience_and_register`: Formal French commercial contract; France; neutral professional register.
- `editing_scope`: Proofreading plus clearly labeled optional style note.
- `protected_terms`: “Service Level Agreement”; citation “Article 4.2”; party names ACME SAS and Beta SARL.
- `output_mode`: Correction table; do not edit source file.
- `scope_and_as_of`: Synthetic facts only; current law/applicability unverified unless explicitly supplied.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/relecteur-christophe-quezel-ambrunaz/SKILL.md

**Worked task output**
Correction table: original “Les partie signataire s’engage à transmettre leurs document.” → “Les parties signataires s’engagent à transmettre leurs documents.” Reasons: subject/participle and verb agreement; possessive-noun number agreement. Optional style: none needed. Preserve “Service Level Agreement,” citation “Article 4.2,” and party names ACME SAS/Beta SARL unchanged. Draft suggestions only; no legal sufficiency opinion or file edit.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
