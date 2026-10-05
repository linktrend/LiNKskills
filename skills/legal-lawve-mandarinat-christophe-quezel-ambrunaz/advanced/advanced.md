# Legal Teaching Material Design: active task method

## Trigger and required inputs

Create or update a defined law-course lesson, tutorial or practical-class teaching pack from instructor-supplied learning objectives and source materials. Research memos, proofreading and QCM generation remain separate tasks.

Required typed fields: `course_and_audience`, `learning_objectives`, `topic_and_legal_scope`, `instructor_sources`, `deliverable_format` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Choose one requested teaching deliverable and capture course, learner level, session duration, prior knowledge and assessment mode. Route standalone QCM, source research, proofreading and book updates to their specific tasks.
2. Translate each learning objective into an observable student action. Match activities and evidence of learning to the objective; remove content that does not serve the class goal.
3. Use only instructor-provided or currently verified legal sources. Record jurisdiction, authority, date and level of certainty. Do not teach an archived legal rule as current without checking primary text.
4. Sequence the lesson: retrieval/prerequisite, concise concept explanation, worked legal reasoning example, guided practice, independent exercise, feedback and summary.
5. Create a fictional fact pattern that tests one or two concepts without copying real personal data. Provide instructor-only answer reasoning with source pinpoints and plausible alternative arguments.
6. Check accessibility, workload, language, timing and alignment with the syllabus. Mark factual/legal uncertainty and local-curriculum choices for instructor approval.
7. Deliver the requested teaching pack as a draft. Do not upload to an LMS, represent the material as official curriculum or claim student outcomes.

## Output contract

Return a JSON-compatible object with these fields: `session_plan`, `learning_objective_map`, `teaching_sequence`, `exercise_and_answer_outline`, `source_and_currency_notes`, `instructor_review_questions`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/mandarinat-christophe-quezel-ambrunaz/SKILL.md`
- Source entrypoint SHA-256: `d16a2405ab2872d89db8cf14eb33f7ea32fb04093b1e301f99eae410dca9804f`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/mandarinat-christophe-quezel-ambrunaz/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Objectives, activity and assessment align.
- [ ] Legal teaching content has a jurisdiction and as-of source.
- [ ] Student-facing exercise is distinct from instructor-only answer notes.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
