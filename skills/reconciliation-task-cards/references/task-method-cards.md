# Reconciliation task routing

Select exactly one task skill; this selector does not reconcile records or produce a workpaper.

- Bank statement versus cash GL: `bank-reconciliation`.
- One GL control account versus aligned subledger: `gl-to-subledger-reconciliation`.
- Reciprocal due-to/due-from between two entities: `intercompany-reconciliation`.

If ambiguous, ask which records/sides and entity relationship are involved. Journal preparation, variance decomposition and elimination/posting remain separate authorized tasks.
