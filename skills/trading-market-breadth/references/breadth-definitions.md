# Breadth and market-state method definitions for successor v0.1.1

Status: independently authored consolidation of definitions from exact pinned source variants. This reference records source conventions so the full approved scope is preserved. It is not a qualified signal, data adapter, policy or canonical runtime dependency.

## Common observation contract

Each supplied series needs instrument/index, venue/exchange calendar, session date/timezone, as-of/publication timestamp, source, units, currency if relevant, adjustment convention, transformations/version and available history. Add only the inputs needed by each family:

- Ratio family: point-in-time membership, inclusion/exclusion rules, member closes and sufficient lookback for its declared moving average; valid count, missing/stale securities and denominator. OHLCV is unnecessary unless another selected measure needs it.
- Distribution-day and FTD families: complete session-ordered daily OHLCV for the named index/proxy, volume units/convention and adjustment rules; sequence/lookback requirements differ by variant.
- Top-factor family: only the selected factor series (leadership, sector relative performance, index moving averages, volatility/sentiment, etc.), with definitions, timestamps and sources.

Use a benchmark only for a requested relative-return/cross-asset comparison. The named point-in-time universe is the denominator and context for ratio-family measures. An unavailable family is reported independently. A missing OHLCV/DD history does not suppress a valid close-only breadth ratio; current-only membership cannot be represented as point-in-time history.

## Close-based uptrend ratios

For each named point-in-time universe U, date t, lookback n, and close/SMA price basis, report numerator N = eligible members with valid close and a valid declared SMA_n for which close_t > SMA_n,t. Denominator D = eligible members with both valid current close and full required history. Ratio (%) = 100 × N / D. Also provide D / eligible universe size, exclusions, missing symbols, delisted constituents handling, corporate-action adjustment and SMA calculation. The pinned uptrend reference uses 20-, 50- and 200-session trend predicates and a source-specific screener universe; do not infer that a current screener is historical membership. Do not label the ratio as broad-market participation without universe coverage. Preserve each horizon separately and do not substitute an eight-day or ten-day smoothing without naming the source series and period.

## Named breadth index and chart families

The pinned market-breadth index is a proprietary/source-defined normalized series with its own 8-session and 200-session averages, historical percentile and divergence constructs. Its scale is not automatically a percent of companies. Record raw index value and both smoothing definitions separately; compute a moving average only from complete chronological observations. The source’s six-factor 0–100 weighted model, fixed colors/zones, adjustment rules and exposure advice are not accepted as Jane thresholds.

The chart reference has two different panels: (A) S&P 500 breadth-index versus long moving average; (B) US uptrend-stock ratio. They require different sources and denominators. Label axis units, index/ratio scale, universe, moving average, displayed time range and missing data; never combine their scores or visually imply same units. Source-specific reversal/positioning arrows and claimed strategy performance are excluded.

## Distribution-day variants

The IBD-style pinned variant uses a close-to-prior-close return r_t = (close_t / close_(t-1)) - 1. Candidate event when r_t <= -0.002 and volume_t > volume_(t-1), for the chosen named index/proxy and volume definition. Maintain one event row with original close/volume, age in exchange sessions, expiry, invalidation basis, and first post-event crossing session. Source configuration has a 25-session expiration and 5% advance invalidation from event close; record whether “advance” uses intraday high or close. Its count buckets treat age 0..N as inclusive, which differs from natural-language “last N sessions.” State the exact source variant, aging convention, adjustment and lookback used.

Stalling day is a separate source disagreement: the IBD monitor explicitly excludes it; market-top source counts some stalling days as half units. Do not include it in the primary DD count. If asked for the alternate source count, show a separate series and source label; define “flat” and volume-up from that source and retain half-count arithmetic. Cluster labels and cutoffs remain unvalidated heuristics, not recommendation gates.

## Follow-through-day variants

Maintain a state machine per index/proxy and per source variant. Inputs include a recent high, low/close, full chronological sessions, OHLCV, day-1 price range, and complete continuation through the maximum window. Preserve candidate correction, swing low, rally-start, invalidation, event day and volume comparison in output.

- Pinned FTD-method variant: correction at least 3% below recent high and at least three down sessions; swing low selected from closing prices; Day 1 and rally integrity use the source’s stated rules; qualify on rally day 4 through 10 when daily gain is at least 1.25% and volume exceeds prior-session volume. Label days 4–7 versus 8–10 separately. The source also supplies an alternative Day-1 rule and post-FTD monitoring criteria; record the chosen rule and do not mix them silently.
- Pinned market-top/chart variant: describes first up-close as rally Day 1 and emphasizes a day 4–7 gain of at least 1.5% on higher volume. Its rally reset/confirmation wording is not identical to the FTD-method variant. Calculate independently or mark unresolved.

Neither source’s success rate, “most important” language, confidence score, or exposure instruction has been qualified. Do not give a false probability or automatic re-entry conclusion. If only close data exist but no volume, report the price progression and mark FTD qualification unavailable.

## Market-top factor rows

Keep six source-derived evidence families as unweighted rows: distribution activity; leadership deterioration; defensive/cyclical sector rotation; breadth divergence; index price/trend structure; sentiment/speculation. State each factor’s actual source, defined lookback and interpretation. A missing sentiment or leadership series removes that factor row only. Do not use a 0–100 composite or risk band. A divergence statement must define “index near high,” benchmark and comparison window; a rotation statement must specify sector taxonomy and return basis; moving averages must state close/adjustment/window. Compare evidence for and against and distinguish top risk, an active correction and bottom/rally evidence.

## Source identity and release boundary

Definitions were reviewed from dr-pabs/Agent-claude-trading-skills commit 4ff3f81c176e46449e388d15676643d4b714a3da, root MIT LICENSE SHA-256 87c93cde8c3a000c19b0c790cd4f7a4e4cb8da5bc6b11e0939bf6df99e245d15. Exact reviewed support paths and SHA-256 values are listed in sibling source-integrated-method.md. The text here is an independent, paraphrased contract: no upstream formulas/code blocks, chart graphics, tables or source scores are copied. No live data, script or provider is used. Retain original source-release flags and do not claim legal or performance clearance.
