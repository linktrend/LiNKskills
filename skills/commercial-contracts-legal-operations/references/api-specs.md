# Source and playbook contract

This is an abstract evidence contract, not a legal-system, e-signature, document, or court-filing API. It contains no endpoint, credential, account binding, or real matter data.

## Existing-overlap and source review matrix

This packet reuses existing read-only catalog patterns where they fit and does not copy
legal text. The review is an engineering provenance record, not legal advice or a
determination that any source applies to a particular matter.

| Existing overlap or source | Reuse decision | Provenance and licence | Security and privacy review | Maintenance owner and trigger |
| --- | --- | --- | --- | --- |
| `compliance-guardian` skill patterns | Reuse evidence and escalation vocabulary only; keep contract preparation read-only | Internal catalog pattern; no external licence claim | Synthetic references only; no credentials or matter contents | Librarian; review when the shared evidence contract changes |
| `citation-enforcer` skill patterns | Reuse source-reference and confidence conventions only | Internal catalog pattern; no copied legal content | References are treated as untrusted input and never executed | Librarian; review when citation fields or validator rules change |
| `search-strategy` skill patterns | Reuse bounded source-discovery language only; no live search adapter | Internal catalog pattern; no external licence claim | No network, account, or private-system access is exposed | Librarian; review when source retrieval policy changes |
| [Anthropic Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms) | Named official legal source for a source receipt when an owner supplies it; applicability remains unverified | Anthropic proprietary terms; store only URL, retrieval time, claim, and digest, not copied text | Treat imported terms as untrusted evidence; do not include account, customer, or contract data | Owner/lawyer; re-check the official page and effective date before each consequential review |
| [Anthropic Privacy Policy](https://www.anthropic.com/legal/privacy) | Named official privacy source for a source receipt when privacy handling is in scope | Anthropic proprietary policy; store reference metadata and digest only | Reject restricted/live-looking fixture material; do not infer a privacy conclusion | Owner/lawyer; re-check when the official policy or data flow changes |
| [Anthropic Consumer Terms](https://www.anthropic.com/legal/consumer-terms) | Named official source only for a supplied consumer-service context; never assume that context | Anthropic proprietary terms; no text copied into this skill | No consumer account data, credentials, or private matter data in fixtures | Owner/lawyer; re-check the source and service context before use |

Official-source receipts therefore require a URL, `source_kind: official`, provenance,
licence, retrieval timestamp, content digest, and owner/applicability review. An absent,
stale, or conflicting receipt is an escalation condition and cannot authorize acceptance,
signature, notice, filing, renewal, termination, or a legal conclusion.

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

### Exact rollback target

PKT-17 has no prior qualified release or live pointer. The exact rollback target is:

`ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614`

This identity represents no prior qualified PKT-17 release.

Rollback means discard the unapproved local artifact and restore that absent state. It
does not create a release, change a catalog pointer, contact a counterparty, or mutate a
legal record.
