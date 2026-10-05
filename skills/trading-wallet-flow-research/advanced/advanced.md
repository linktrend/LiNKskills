# Method notes

## 1. Freeze the chain, wallet/cohort rule, token identity, venue/program scope, observation interval and cutoff

Freeze the chain, wallet/cohort rule, token identity, venue/program scope, observation interval and cutoff. Preserve raw event IDs and provider/source versions.
## 2. Normalize amounts using token decimals and quote/base conventions; convert timestamps and slots without silently merging block time, provider time and observation time

Normalize amounts using token decimals and quote/base conventions; convert timestamps and slots without silently merging block time, provider time and observation time. List incomplete pages, rate-limit gaps, failed lookups and coverage.
## 3. Classify each event as swap, transfer, deposit, withdrawal, LP add/remove, airdrop, bridge, fee, reward, or unresolved

Classify each event as swap, transfer, deposit, withdrawal, LP add/remove, airdrop, bridge, fee, reward, or unresolved. Do not count transfers or LP movements as realized trade P&L. Maintain opening/closing inventory.
## 4. Reconstruct candidate trade lots from swap events and reconcile provider-reported P&L to sampled raw transactions

Reconstruct candidate trade lots from swap events and reconcile provider-reported P&L to sampled raw transactions. State lot-matching convention, treatment of partial exits, fees, priority costs and mark prices. Unknown basis remains unknown, not zero.
## 5. Calculate only supported metrics: closed-trade count, win rate, gross/net P&L, profit factor, realized/unrealized split, holding-time distribution, drawdown if a dated equity series exists, and median/dispersion

Calculate only supported metrics: closed-trade count, win rate, gross/net P&L, profit factor, realized/unrealized split, holding-time distribution, drawdown if a dated equity series exists, and median/dispersion. Define zero-loss and empty-sample results as undefined/infinite per metric, not arbitrary caps. Include denominators and sample sizes; avoid claiming statistical significance from a fixed trade minimum.
## 6. Describe style, token/protocol focus, trade-size bands and bot-like timing as heuristics

Describe style, token/protocol focus, trade-size bands and bot-like timing as heuristics. Show evidence (interval variability, repeated sizes, hours, protocol usage) and non-automated explanations; do not assign a human/bot identity or behavioral intent.
## 7. Test concentration by token and top winner, leave-one-out results, recency vs earlier windows, funding/co-trade/bundle links, and position size relative to contemporaneous volume/liquidity

Test concentration by token and top winner, leave-one-out results, recency vs earlier windows, funding/co-trade/bundle links, and position size relative to contemporaneous volume/liquidity. Same funder or same-slot activity is a possible link, not proof of common control or wash trading. Enumerate likely false positives such as exchanges, market makers, airdrops, shared custodians and bots.
## 8. Close with gaps, sensitivity to missing history and marks, and an informational watchlist/monitor/exclude recommendation only when criteria were provided

Close with gaps, sensitivity to missing history and marks, and an informational watchlist/monitor/exclude recommendation only when criteria were provided. No copying, sizing, order, subscription, monitoring deployment or auto-exit.