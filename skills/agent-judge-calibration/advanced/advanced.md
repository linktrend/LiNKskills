# agent-judge-calibration — method selection and source boundaries

Both sources perform the same task: rubric/LLM judge calibration and paired comparison. Murat advanced-evaluation is the strongest base for evidence-first prompts, explicit bias controls, stable-ID position swaps and confidence/ties. Incorporate Borghei independently anchored multi-grader agreement, aggregation boundaries, fixed-batch versus streaming rankings and intransitivity review. General dataset/regression evaluation and actual external paid model execution remain separate.

## Integrated task controls

1. Select deterministic checks when they establish the property. For remaining judgments, choose direct scoring against objective reference criteria or pairwise comparison for preferences; isolate one measurable property per criterion and anchor every scale point before scoring.
2. Require cited observable evidence before each score, with structured criterion-level rationale. Separate factual correctness, style and safety; confidence, authority, verbosity or length cannot substitute for evidence.
3. Use independently labeled held-out calibration examples, at least two reviewers where available, and analyze disagreement by criterion and slice. Human labels can be wrong; reconcile evidence rather than call disagreement proof of evaluator failure. Report unavailable calibration as a blocker to trust, not a passed judge.
4. For pairwise evaluation run both A/B and B/A orders, map display positions back to stable candidate IDs, and count a consistent winner only after that remapping. Disagreement becomes TIE/escalation with reduced confidence, not a forced majority from two votes.
5. Control position, length, verbosity, self-preference and authority biases; calibrate confidence against evidence, human agreement and observed consistency. A different judge family is a mitigation, not independence proof. Sensitive grading inputs remain restricted; model calls require current authorization and budget.
6. Analyze per-criterion agreement and ranking robustness. Use order-independent fixed-batch ranking when appropriate, sequential ranking only for its intended setting, and inspect intransitive cycles; do not treat rankings or confidence values as calibrated probabilities without evidence.
7. Version judge prompts, anchors and calibration sets. Recheck stability on prompt/model/tool or domain changes, route unresolved/safety-sensitive judgments to authorized review, and report measured quality with observed cost/latency; do not certify an agent from a judge design document.

Complete source copies remain evidence; do not execute unreviewed source scripts.
