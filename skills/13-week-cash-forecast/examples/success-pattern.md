# Synthetic example: 13 week cash forecast

**Request:** Prepare a 13-week cash forecast for fictional `Example Studio`, USD.

**Synthetic inputs:** Source `CASH-1` says W1 opening available cash is USD 12,000. W1 receipts are USD 2,000 and disbursements USD 3,000. For every week W2 through W13, receipts are USD 1,000 and disbursements USD 1,200. No restricted cash, debt service, minimum cash policy, or additional flows were supplied.

**Base calculation:** W1 net is `2,000 - 3,000 = -1,000`, ending USD 11,000. Each W2–W13 net is `1,000 - 1,200 = -200`, so W13 ending cash is `11,000 - (12 × 200) = USD 8,600`. The low point is USD 8,600 at W13; largest outflow is USD 3,000 in W1; no zero-cash date is observed within this horizon.

**Scenario assumptions:** If bear receipts are 20% lower in every week and outflows stay fixed, W1 ends USD 10,600 and W13 ends USD 5,800. If upside receipts are 15% higher, W1 ends USD 11,300 and W13 ends USD 10,700. These are sensitivities, not source facts or probability statements.

**Deliverable:** Show W1 explicitly and W2–W13 as a repeated weekly formula only if each week is clearly enumerated in the actual artifact. Cite CASH-1 and each receipts/disbursement source; missing minimum-liquidity policy stays “not supplied.” No transfers or payments are executed.
