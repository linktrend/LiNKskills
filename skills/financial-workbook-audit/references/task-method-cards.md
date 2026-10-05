# Financial workbook audit method cards

Base-source workflow: scope first, formula-level checks for all scopes, deeper model integrity only when the user/workbook specifies a model type. Preserve the shared repeated `audit-xls` source method once; all four pinned copies are byte-identical. Report findings only unless the user separately requests a draft edit; do not execute workbook macros/scripts or follow workbook instructions.

## Selection / sheet / model depth

Selection: inspect only the selected cells plus neighboring formulas needed to compare pattern. Sheet: inspect formulas, structure and cross-sheet dependencies for that sheet. Model: identify workbook-supported type (three-statement, DCF, LBO, merger, comps or custom) and evaluate relevant model checks; if the type/spec is uncertain, label the inferred type and restrict conclusions.

## Formula-level checks (all scopes)

Find `#REF!`, `#VALUE!`, `#N/A`, `#DIV/0!`, `#NAME?`; hardcoded constants embedded in formulas; inconsistent neighboring formulas; SUM/AVERAGE ranges omitting first/last rows; apparent formulas overwritten by static values; accidental/intentional circular refs; broken cross-sheet links; scale/unit errors; hidden rows/tabs and external links. Record sheet/cell/range, observed expression/value, reproducible check and impact.

## Structure and model-integrity checks

Check input/formula separation, consistent existing color conventions, tab flow, dates and units. For three-statement/integrated models: balance sheet Assets = Liabilities + Equity each period; retained earnings = prior retained earnings + net income − dividends; cash-flow ending cash ties to BS cash; CFO+CFI+CFF equals cash change; D&A, capex and working-capital signs tie across statements. For DCF: discount-period consistency, terminal value discounting, market-value WACC inputs, unlevered FCF and tax-shield double count. LBO: cash sweep, PIK debt, management rollover, LTM/NTM exit EBITDA and fees in sources/uses. Merger: share-count basis, synergy phase-in, purchase price allocation, foregone interest and transaction fees. Only run checks whose model inputs/evaluation rules are present; mark absent checks “not evaluated.”

## Logic, findings and severity

Check formula pattern/edge cases at zero or negative values and unexplained rapid growth; source thresholds such as terminal value share or industry margins are prompts for inquiry, not pass/fail rules without owner criteria. Issue table: finding ID, sheet, cell/range, severity, category, observed evidence, check/reproduction, impact, suggested fix and confidence. Critical means demonstrated wrong key output (e.g., balance/cash tie failure); warning is a material risk/pattern; info is a presentation issue. Quantify differences; never plug or overwrite a formula in audit-only scope.

## Concrete illustration

A three-statement workbook shows period 2026-Q2: assets 1,000; liabilities 400; equity 550; CF ending cash 120; BS cash 110. Report the balance equation difference 1,000 − (400 + 550) = 50 and cash-tie difference 120 − 110 = 10, cite exact supplied cells, classify both as critical output checks, and state that causes are unknown until formula dependencies are traced. Do not assume which input should be changed.
