# Worked synthetic success example — legal-lawve-az-eu-website-privacy-audit-mirza-chiragov

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `site_materials`: Synthetic site: az-example.test, privacy text dated 2024-03, banner screenshot shows Accept and Settings, no refusal button visible.
- `site_languages`: Azerbaijani and English; only English supplied.
- `audience_and_market`: Founder says AZ-only; checkout screenshot shows EU country selector; actual targeting unknown.
- `processing_context`: Marketing site with analytics cookie; controller legal entity not supplied.
- `audit_depth`: Evidence table plus concise summary.
- `as_of_date`: Synthetic review date 2026-10-04; current official sources not supplied.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/az-eu-website-privacy-audit-mirza-chiragov/SKILL.md

**Worked task output**
Evidence findings: supplied English privacy text is dated 2024-03; screenshot shows Accept and Settings, with no refusal button visible in that capture. This is “not observed,” not proof no refusal exists. AZ-only market claim conflicts with an EU country selector; actual targeting and GDPR applicability remain unresolved. English-only material cannot complete an Azerbaijani-language review. Obtain full Azerbaijani text, mobile/consent-flow captures, controller identity and current AZ/EU primary authorities; no legal compliance conclusion.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
