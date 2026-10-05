# Worked synthetic success example — legal-lawve-invoice-review-compliance-scott-margetts

**Task:** synthetic-golden from this skill’s `references/eval-suite.json`.

**Case facts**
- `invoice_and_lines`: Synthetic INV-204: 1.5 hours x USD 500 = USD 750 for “review documents, call, admin”; 0.5 hours x USD 300 = USD 150 for “scan and upload”; invoice total USD 900.
- `matter_and_firm`: Matter M-22; Firm Delta; associate rate cap USD 450 in supplied engagement letter.
- `billing_guidelines`: Supplied rule: clerical scanning is non-billable; narratives must separate tasks over 1.0 hour; rates above approved cap require written exception.
- `review_system`: Manual spreadsheet review; no e-billing connector.
- `prior_invoice_evidence`: No prior invoices supplied.
- `scope_and_as_of`: Synthetic facts only; current law/applicability unverified unless explicitly supplied.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/invoice-review-compliance-scott-margetts/SKILL.md

**Worked task output**
Invoice math and flags: line 1 is 1.5 × $500 = $750. The supplied $450 cap is exceeded by $50/hour, or **$75 total** across 1.5 hours; request written exception evidence. “Review documents, call, admin” is a combined 1.5-hour narrative and must be separated under the supplied >1.0-hour rule. Line 2 is 0.5 × $300 = $150 for scanning/upload; the supplied rule makes clerical scanning non-billable. The $150 line amount is the provisional review exposure, subject to confirming whether the full line is disallowed. Invoice total ties: $750 + $150 = $900. Draft review only; no rejection or payment.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
