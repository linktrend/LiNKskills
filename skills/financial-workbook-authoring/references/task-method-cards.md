# Financial workbook authoring method cards

Adapt the pinned `xlsx-author` instructions to supported native artifact creation/edit/readback. Do not claim headless XLSX, openpyxl, Bash, a `./out/` path, or live Excel controls exist unless the current consumer explicitly supplies them. Preserve compatible workbook styling rather than imposing colors; make formula/input separation, useful named references, visible checks and readback explicit.

## Intake and inspect

Capture purpose, audience, period, units/currency, entity, model type, source inputs, assumptions, requested tabs/outputs, existing template, destination and edit scope. Read existing workbook structure and formulas first. If no output format is specified, use the consumer's supported artifact format and state that format; do not invent an export path. Avoid asking for fields already supplied; isolate only material missing inputs.

## Structure and author

Create or edit only the user-authorized draft artifact. Put source inputs and assumptions in clearly marked input areas, calculations in formula cells and linked values as traceable references; use named ranges for key inputs referenced by decks/memos or other sheets when supported by the workbook format. Organize tabs for the requested decision (for a three-statement forecast, e.g. Inputs/Assumptions, IS, BS, CF, Schedules, Checks). Preserve source/cell reference for each material input. State every scenario assumption and do not add unsupported data.

## Visible checks and output QA

Add a visible Checks area/tab appropriate to model type: balance sheet balances, cash flow ending cash ties to balance-sheet cash, statement/schedule tie-outs, totals and range/coverage checks. Show `PASS`, `FAIL` or `NOT TESTED` with a formula/evidence reference; failures remain visible, never patched by a balancing plug. Use a consistent existing color legend if the template already has one; if a color convention is requested or adopted, label it (input/formula/cross-sheet link) and apply consistently. Do not insert named ranges or styles unsupported by native format.

After writing, read the artifact back with the supported native read interface. Confirm required sheets/sections, row/column dimensions, formula presence, key outputs, formulas' source references, checks and destination. If readback cannot expose formulas, state the precise limitation and provide a structural preview. Return a draft summary and remaining owner choices. No posting or external transmission.

## Concrete illustration

Synthetic one-period operating model, USD: source inputs revenue 100,000, growth 10%, COGS rate 40%, operating expense 45,000. Formula outputs: forecast revenue = 100,000 × (1+10%) = 110,000; forecast COGS = 110,000 × 40% = 44,000; gross profit = 66,000; EBITDA = 66,000 − 45,000 = 21,000. Inputs stay distinct from formula outputs. Checks show revenue roll-forward and gross profit/EBITDA arithmetic; user-supplied business meaning and period remain labeled. Read back the drafted workbook and confirm these outputs before handoff.
