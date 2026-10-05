# Proposed adversarial cases

## panel-dimension

Input: Weights are a time×asset matrix; a naive diff over axis 1 is described as turnover.

Expected: Flag dimension error: turnover is computed across time for each asset before aggregation, never across neighboring assets.

## locate-failure

Input: A short’s point-in-time locate is unavailable, but source model treats it as 200 bps extra slippage.

Expected: Model as a skipped/missed entry (or explicit scenario); do not treat unavailable borrow as a fill.

## spread-units

Input: Full quoted spread is 40 bps, with entry and exit each assumed to cross the market.

Expected: Charge 20 bps half-spread per side or 40 bps round-trip for the two halves; state convention and do not double count to 80 bps.

## missing-adv

Input: A strategy input provides price and weight change but no ADV units/currency.

Expected: Derive notional/quantity if inputs support it, but mark participation/capacity unresolved; do not substitute a universal floor.
