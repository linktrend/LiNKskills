# Changelog

## 0.1.0 — 2026-10-04

- Split gap ingestion/deduplication/notice proposals from the separate register status/close/accept proposal task.
- Added typed contracts, synthetic fixtures and proposal-only scope.

## 2026-10-05 — completion contract and runtime precedence

- Tightened completed-draft requirements around non-empty task-specific sections and evidence; added typed missing-input, unknown-fact, and partial-work fields for `needs_context`.
- Added task-shaped completed, partial, and empty-completed contract fixtures; updated JSON/YAML eval criteria.
- Clarified OpenClaw consumer-owned SQLite checkpoint precedence over portable JSONL template metadata.

- 1.0.0 pre-publication correction (2026-10-05): Align task-specific examples and input-contract validation where applicable; preserve copied source bytes and notices. This records source correction only, not qualification, publication or behavioral acceptance.
