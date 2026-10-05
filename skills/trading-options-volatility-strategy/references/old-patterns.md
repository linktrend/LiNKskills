# Known source-pattern hazards

Options-advisor defaults historical volatility when IV missing, although HV is not a market-implied substitute; rates are hard-coded/date-stale; examples claim profit probability from finite grid or unsupported calibration; theta/rho/vega units vary by day/per 1% and multiplier; American exercise/settlement, discrete dividends, multiplier/deliverables, early assignment and corporate actions need exact contract terms. Example strategies include contradictions and unsafe adjustments (adding another spread after adverse move); coverage omits path-dependent/borrow/margin and surface dynamics. 0DTE-flow includes direct Tradier order cURL/token/account ID and live rules; exclude entirely from active procedure. Volatility-modeling assumes 365-day crypto annualization and regime bands; not imported for equities. LSEG/LLMQuant tool names are not available native tools; use supplied chain/vol data only.

## Repair rule

Separate verified observation, calculation, inference, scenario, and advisory. Never infer successful evaluation from structural validation.
