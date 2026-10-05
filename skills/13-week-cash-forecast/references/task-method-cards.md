# 13-week cash forecast method cards

These cards preserve operational branches from the pinned CrewM8 cash-forecast source, adjusted for evidence and jurisdiction limits. Use only the cards relevant to the request. Original is preserved under `upstream/gokulsvision--crewm8-cfo-skills@c814ff97743e/skills/cash-treasury/cash-forecasting/SKILL.md`.

## Card A — Dated cash receipt schedule

For each receipt retain customer/category, invoice or contract reference, expected cash date, amount/currency, source and timing basis. Reconcile invoice/AR balance to customer cash expectations, but do not equate revenue recognition with cash. Model collection timing with prior customer/segment history only when current and comparable. Mark new pipeline separately and use owner-supplied conversion/timing assumptions. If payment processors are used, model actual settlement delay from current processor evidence. Source suggestions such as 30–45 day collection or enterprise 45–60 days are not universal defaults; request an assumption or show a sensitivity range.

## Card B — Dated cash disbursement schedule

Use pay dates from payroll calendars, approved AP due dates, actual recurring billing dates, executed service/debt schedules, and current applicable tax calendars. Keep a commitment/source ID, expected cash date, amount, currency and confidence basis for each line. Preserve quarterly/annual lumpiness. Spread a budgeted recurring cost weekly only when the amount is truly a regular weekly assumption and label it as such. Do not apply a source's sample U.S. tax dates to an entity without confirming jurisdiction and current primary authority.

## Card C — Weekly roll-forward and liquidity markers

For week `t`, compute `net_t = sum(receipts_t) - sum(disbursements_t)` and `ending_t = opening_t + net_t`; set `opening_(t+1) = ending_t`. Independently recompute every row. Identify minimum ending cash and its week, largest disbursement week, net change from opening through W13, and first negative ending balance within W1–W13. If none occurs, state `not observed within the modeled horizon`; beyond-horizon runway requires separately stated assumptions. Restricted cash, uncleared deposits or unavailable facilities stay distinct from available cash.

## Card D — Scenarios

Each scenario is a transparent delta table keyed by week/category/source line. Apply owner-requested shocks (for example a named-customer loss, hiring start date, collection delay or receipt reduction) only to matching lines; re-run the full weekly roll-forward. Show base values, scenario values and ending-cash differences. Do not claim universal probabilities such as 80% confidence, or invent minimum liquidity policy. State whether the variant is a factual commitment, sensitivity assumption or owner decision.

## Card E — Forecast accuracy and weekly update

For forecast-vintage `v`, compare each source line's forecast amount/date against subsequent actual bank cash date/value. Report `actual - forecast`, amount error and timing displacement separately; calculate percentage error only where the forecast denominator is nonzero and meaningful. Preserve the old forecast and actual evidence IDs. When rolling forward, add one new week, drop the elapsed horizon week only after retaining the prior-vintage comparison, update dated inputs, and list changes to assumptions and the resulting liquidity low point. This work prepares recommendations; it does not modify books, budgets or payment schedules.

## Source map

- Original `Procedure` steps 1–3 and `Quick Reference`: weekly inflow/outflow categories, cash timing, net flow, ending cash and zero-cash calculation (adapted to require evidence-backed dates and remove implied defaults).
- Original `Scenario Analysis`, `Key Metrics`, `Pitfalls`, `Verification`, and user examples: base/downside/upside variants, runway/low point/largest outflow, settlement lag, lumpy items, customer-loss and new-hire scenarios, and forecast refresh.
- Original U.S. example tax dates, assumed confidence levels and example company amounts are not adopted as factual rules or defaults.
