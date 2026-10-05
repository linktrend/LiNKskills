# Known failure patterns

- Source thresholds conflict (30 vs 50 trades) and are not universal evidence thresholds: report sample size and uncertainty rather than a fixed pass bar.
- Composite scores combine arbitrary weights, mix decimal fractions with percentages, and can hide missing/empty denominators; do not compute or inherit them.
- Provider P&L can misclassify transfers, open inventory, partial closes or missing cost basis; reconcile raw samples and label unresolved basis.
- Wallet labels such as bot, insider, smart money or sybil imply identity/intent; downgrade to observable behavior signals and alternatives.
- Same-slot buys, shared funder and repeated amount are correlates with substantial false positives; never call them proof of coordination.
- Upstream scripts, APIs, websocket monitors, score-based watchlists, proportional sizing, copy execution and stop-loss instructions are excluded; no new provider or credentials.
- Treating a research draft or fixture as a trade recommendation, authorization, evaluation receipt, or certification.
- Writing JSON/JSONL runtime sidecars instead of using native session and approved Program Ledger.
