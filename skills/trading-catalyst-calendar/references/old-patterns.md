# Source audit repair rules

- Treat source-provided score bands, thresholds, probabilities, sizing, and historical validation as claims until their definitions and evidence are independently checked.
- Preserve source variants as separate provenance branches when their rules differ; never silently blend thresholds.
- Keep dates, units, calendar, universe, data vintage, and cost assumptions attached to values.
- Distinguish advisory recommendation from order submission or live activation.
- Never execute source scripts until the implementation and dependency contracts receive separate review.
