# Proposed adversarial cases

These fixtures are proposed and not run.

- **wrong-way-stop:** Input: Long entry 100 stop 110. Expected: Reject side mismatch; do not abs() distance.
- **fx-missing:** Input: GBP contract but NAV is USD and FX unavailable. Expected: Leave converted risk/size unresolved; no silent 1:1.
- **round-up:** Input: Raw size 9.7, lot step 1, budget 100. Expected: Round down to 9, recompute risk and constraints.
