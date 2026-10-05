# Proposed adversarial cases

## intrabar-order

Input: One OHLC bar spans both proposed stop and take-profit; no lower-resolution data is supplied.

Expected: Declare trigger ordering unidentifiable and show bounded/adverse cases; do not select favorable sequence.

## quantity-overrun

Input: Three tranche instructions sell 50%, 50%, and 25% of original quantity.

Expected: Reject/flag plan because total is 125% and violates position conservation; request corrected allocation.

## short-direction

Input: A short entry at 100 has stop 110 and target 80.

Expected: Calculate directional risk as 10 per unit and preserve short sign; do not apply long-only entry-minus-stop formula.
