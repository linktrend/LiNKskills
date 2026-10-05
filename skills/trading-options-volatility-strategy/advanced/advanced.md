# Options strategy and volatility research: method notes

## Source audit repairs

Options-advisor defaults historical volatility when IV missing, although HV is not a market-implied substitute; rates are hard-coded/date-stale; examples claim profit probability from finite grid or unsupported calibration; theta/rho/vega units vary by day/per 1% and multiplier; American exercise/settlement, discrete dividends, multiplier/deliverables, early assignment and corporate actions need exact contract terms. Example strategies include contradictions and unsafe adjustments (adding another spread after adverse move); coverage omits path-dependent/borrow/margin and surface dynamics. 0DTE-flow includes direct Tradier order cURL/token/account ID and live rules; exclude entirely from active procedure. Volatility-modeling assumes 365-day crypto annualization and regime bands; not imported for equities. LSEG/LLMQuant tool names are not available native tools; use supplied chain/vol data only.

## Source support closure

Personally read/copy exact TM Black-Scholes methodology; LLMQuant options strategy, Greeks, P&L simulator and volatility-surface workflow; and LSEG option-vol-analysis entrypoint. LLMQuant workflows depend on LLMQuant Data capabilities not established as available; LSEG names MCP tools not exposed, so no tool call/paid access is assumed. Options-pricing support remains crypto-oriented/stub; unreviewed Black-Scholes code and additional planned feature docs are not adopted. No scripts/tests run.
