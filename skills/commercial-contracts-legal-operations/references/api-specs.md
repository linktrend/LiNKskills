# Source and playbook contract

This is an abstract evidence contract, not a legal-system, e-signature, document, or court-filing API. It contains no endpoint, credential, account binding, or real matter data.

## Source receipt

An owner may provide `source_ref`, `source_kind`, `provenance`, `licence`, `retrieved_at`, `content_digest`, and `authority_status`. The skill records only synthetic references and hashes. Official sources are preferred but still require applicability and jurisdiction review.

## Playbook receipt

An approved playbook receipt contains `playbook_ref`, `version`, `owner`, `approval_status`, `licence`, and `content_digest`. Comparison is a read-only preparation returning `match`, `gap`, `unclear`, or `not_applicable`. A receipt is not legal advice, sign-off, or permission to accept a gap.

## Effect vocabulary

| Effect | Skill output | Prohibited action |
| --- | --- | --- |
| `read` | Request a supplied source or owner evidence | Querying a private legal system directly |
| `prepare` | Draft summary, register, comparison, or escalation | Publishing a legal conclusion |
| `sign` / `accept` | Always false; human review required | E-signature or contract acceptance |
| `send` / `file` | Always false; draft only | Notice, filing, email, or counterparty delivery |
| `mutate` | Always false | Changing a contract, matter, deadline, or renewal record |

## Jurisdiction and privacy

Jurisdiction and governing-law claims are source data, not inferred defaults. Unknown, conflicting, or materially consequential jurisdiction routes to a lawyer or Principal. Fixtures and telemetry contain no real contract text, customer identifiers, privileged material, credentials, or private company data.

## Failure and rollback

Classify unavailable, malformed, unauthorized, jurisdiction-ambiguous, and privacy-rejected evidence separately. Retry only idempotent local reads. On failure return `FAILED` or `PENDING_APPROVAL`, a safe next action, source hashes, and a prior-release/state rollback pointer. Rollback discards an unapproved artifact and never sends a rescission or mutates a legal record.
