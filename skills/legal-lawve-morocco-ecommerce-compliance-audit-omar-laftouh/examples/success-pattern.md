# Worked synthetic success example — legal-lawve-morocco-ecommerce-compliance-audit-omar-laftouh

**Task:** synthetic-golden from this skill’s `references/eval-suite.json`.

**Case facts**
- `site_and_capture`: Synthetic `shop.ma` capture 2026-10-05: homepage, product page, footer and checkout screenshots; no mobile capture.
- `operator_and_market`: Moroccan seller ships domestically; marketplace status unknown; payments handled by third party.
- `privacy_evidence`: Privacy page dated 2023 says “we may share data”; banner shows Accept and Settings, refusal path not captured.
- `consumer_terms_evidence`: Price and delivery shown; return/withdrawal terms link returns 404; seller contact has email only.
- `authority_snapshot`: No current official Moroccan legal or CNDP sources supplied.
- `scope_and_as_of`: Synthetic facts only; current law/applicability unverified unless explicitly supplied.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/morocco-ecommerce-compliance-audit-omar-laftouh/SKILL.md

**Worked task output**
Capture-based findings: pages observed are homepage, product, footer and checkout on 5 Oct 2026; mobile was not captured. Privacy text is dated 2023 and says data “may be shared”; consent screenshot shows Accept/Settings, refusal path not captured. Return/withdrawal link returned 404 in this capture, which is not proof that terms do not exist. Seller ships domestically; marketplace role and backend processing unknown. Obtain current Moroccan/CNDP primary sources and full-language/mobile evidence before legal conclusions; no statutory period or filing duty asserted.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
