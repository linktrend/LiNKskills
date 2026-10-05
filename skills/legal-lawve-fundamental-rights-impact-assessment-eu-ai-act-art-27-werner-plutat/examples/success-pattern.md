# Worked synthetic success example — legal-lawve-fundamental-rights-impact-assessment-eu-ai-act-art-27-werner-plutat

**Task:** synthetic-golden from this skill’s `references/eval-suite.json`.

**Case facts**
- `system_and_classification`: Synthetic credit score model used by a private EU bank; vendor labels it Annex III point 5(b), no independent classification attached.
- `deployer_status`: Private bank; no public-service status facts supplied.
- `deployment_context`: Scores retail loan applications; human reviewer can override but override rate is unknown.
- `rights_and_risk_evidence`: No affected-group testing; complaint route exists; DPIA covers data protection only.
- `authority_snapshot`: No current Article 27 text supplied.
- `scope_and_as_of`: Synthetic facts only; current law/applicability unverified unless explicitly supplied.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/fundamental-rights-impact-assessment-eu-ai-act-art-27-werner-plutat/SKILL.md

**Worked task output**
Prerequisite and impact map: vendor labels the private EU bank’s retail credit model Annex III point 5(b), but no independent classification or current text is supplied. Private-bank public-service status is unestablished, so do not assume Article 27 FRIA duty. Map affected loan applicants, group-impact evidence (absent), override rate (unknown), complaint route (exists), and DPIA scope (data protection only). Verify high-risk/deployer gates and current Article 27 before deciding applicability.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
