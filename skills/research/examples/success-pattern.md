# Successful research brief (synthetic)

Question: Which official release notes explain the current API change?

- Research Intent: stable scope, currentness required, web tier only, confidence
  threshold 0.8, stop after the official release note and migration guide agree.
- Observed fact: the official release note dated 2026-08-20 deprecates field X
  ([official release note](https://example.com/official-release-note)).
- Observed fact: the official migration guide dated 2026-08-21 shows field Y as
  the replacement ([migration guide](https://example.com/migration-guide)).
- Inference: callers should migrate from X to Y before the stated removal date.
- Recommendation: schedule a compatibility review; the research workflow does
  not change the caller.

The report records retrieval dates, confidence, the claim-evidence matrix, and
the absence of external effects. The URLs are synthetic examples.
