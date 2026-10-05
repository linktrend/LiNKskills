# GL-to-subledger reconciliation

Reconcile one GL control account to its aligned subledger for one entity, period and currency. Bank work routes to `bank-reconciliation`; reciprocal entities route to `intercompany-reconciliation`; variance decomposition and journal preparation are separate tasks.

Inputs: GL control-account detail/balance; same-entity, same-cutoff named subledger detail; supplied mapping, stable references, currency and tolerance if any.

1. Fix entity, account, cutoff, units/currency and both source control totals.
2. Preserve original values; normalize identifiers in separate fields and disclose lossy normalization.
3. Aggregate subledger rows to the same control account/cutoff and bridge to source total.
4. Match exact reference plus amount first. Classify amount/date, manual journal, pending interface, duplicate, mapping, missing-side and data-quality breaks. Use supplied mapping/tolerance; otherwise exact match and show difference.
5. Tie matched plus unmatched lines to each source total; show aging and evidence. Causes remain hypotheses.
6. Return workpaper and adjustment candidates for owner review; do not create or post entries.

Acceptance: every row accounted once; period, entity, signs, units and control totals visible. No unsupported tolerance, policy, cause, system change, posting, payment or external communication.