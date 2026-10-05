# Known failure patterns

- Contradictory tranche percentages may total over 100%; validate sum and conservation against actual remaining quantity.
- Source formulas assume long positions in places; derive direction-aware inequalities and risk distances for short positions separately.
- Static ATR, EMA, PumpFun graduation, volume-decay and time thresholds are examples, not portable rules; require asset/timeframe/source justification.
- Bar-only replay may not identify stop/target ordering, gap-through prices, queue position, spread or available depth; disclose ambiguity instead of fabricating exact fills.
- No order, stop placement, auto-exit, position sizing or claim of guaranteed downside cap.
- Treating a research draft or fixture as a trade recommendation, authorization, evaluation receipt, or certification.
- Writing JSON/JSONL runtime sidecars instead of using native session and approved Program Ledger.
