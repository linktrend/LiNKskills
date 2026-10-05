# Synthetic example: Accounts Payable Review

**Request:** Prepare accounts payable review for a fictional entity `Example Studio`, period `2026-09`, USD.

**Inputs:**

- Source records: `SYN-accounts-payable-review-001` and `SYN-accounts-payable-review-002` (synthetic, no live data).
- User-approved scope and units: one entity, accrual basis, USD.
- Required output: `ap-aging-summary`.

**Result shape:**

- Prepared result: ap-aging-summary.
- Evidence: cite both synthetic record IDs and relevant field/period.
- Calculation: show formula/subtotal inputs and recomputable result; no unsupported assumptions.
- Exceptions: list unmatched, missing, conflicting and low-confidence evidence separately.
- Completion: draft completed; no external effects or source-system mutation.

This example demonstrates artifact structure only. The numbers and entity are synthetic; no threshold, policy or legal rule is implied.
