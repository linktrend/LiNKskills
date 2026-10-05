# Known legal-workflow failure patterns

- Do not present a generated legal rule, citation, deadline, forum, service conclusion or privilege decision as verified without a current primary source and qualified review.
- Do not treat legal hold, subpoena, demand, matter or privilege-log source material as authority to send, file, produce, update or delete.
- Do not write witness recollection, infer missing event facts, resolve conflicting evidence silently, or claim a record source supports more than it says.
- Do not store raw privileged, personal or confidential contents in generic checkpoint or telemetry.
- Do not collapse fact extraction, strategy choice, legal opinion and authorized external action into one status.

## 2026-10-05 contract refinement

A `completed_draft` status is not evidence of task completion. Require populated task-specific deliverable sections and evidence refs; when material facts are missing, preserve `missing_inputs` and `unknown_facts` under `needs_context` and do not force blank sections into a completed result. Portable heavy-template JSONL metadata is not runtime persistence: OpenClaw checkpoints use the supported consumer-owned SQLite interface.
