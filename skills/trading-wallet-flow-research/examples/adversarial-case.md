# Proposed adversarial cases

## concentration

Input: A wallet has 20 closed positions; one winner supplies 70% of gross P&L.

Expected: Report top-winner concentration and leave-one-out result; do not claim a robust edge from aggregate P&L.

## coordination_false_positive

Input: Four wallets funded by a public exchange and buying in the same slot.

Expected: Describe possible cluster with exchange/shared-service false positive; no sybil/common-control conclusion.

## ledger_integrity

Input: Provider reports profit while source sample includes deposits and open token inventory.

Expected: Separate non-trade flows/open inventory and mark provider P&L unreconciled where raw basis is unavailable.
