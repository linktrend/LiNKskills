# Domain-Specific Matter Intake Cards

The nine source methods share the same operations and context-isolation procedure. Use only the relevant card; do not infer facts from its presence. Required common fields: exact matter identifier, client/counterparty, purpose, parties/roles, owner, status, source dates, scope/confidentiality and related references.

## AI governance
Record AI system/use-case name, provider/model as evidenced, affected process/population, data classes, owner, decision sought, applicable policy/contract/regulatory sources and current deployment status. Do not infer regulatory classification or compliance.

## Commercial
Record contract/transaction type, counterparties, company side, deal purpose, versions/attachments, negotiation owner, deadline and governing law exactly as written if provided.

## Corporate
Record entity names and roles only from authoritative company records, corporate action type, decision makers, formation/standing documents, deadlines and required approvals. Do not infer entity status or authority.

## Employment
Record employer/entity, work location(s) evidenced, role, employment event, applicable policy/contract documents and privacy boundary. Minimize employee identifiers and health/accommodation data. Do not assume employment law jurisdiction.

## IP
Record asset/work identifier, creator/owner as supported, assignment/license status, relevant filing/deadline, chain-of-title evidence and dispute/clearance question. Do not create a patent/trademark filing or infer ownership.

## Litigation
Record proceeding/matter number, tribunal/forum as stated, parties/counsel, deadlines, claim/response posture, hold status and source date. Limit access to authorized matter participants; do not merge unrelated matters. A specific litigation portfolio briefing remains a separate deliverable.

## Privacy
Record data subject categories, personal-data types, processing purpose, controller/processor roles as evidenced, regions, incident/rights request timing, source contracts/notices and response owner. Do not make a breach-notification determination without current jurisdiction-specific authority.

## Product
Record feature/use case, launch stage, representations/data flows, users, substantiating evidence, product owner and review deadline. Keep product-risk review distinct from matter context creation.

## Regulatory
Record agency/regime cited in source, jurisdiction, regulated activity, notice/investigation/deadline, evidence record and owner. Do not treat a copied foreign-law source as applicable without fact and authority verification.

## Original-source adaptation and runtime boundary
Each source pack retains its domain-specific matter template, retention, related-matter and cross-context details under `references/upstream/<domain>/`. The original uses `~/.claude` practice configuration and filesystem archive paths; these remain exact provenance only. In Lisa/OpenClaw, operations are conditional on current consumer-owned context/session/artifact capability. No new local files, JSONL, custom database, or profile change. The operating model and feature availability remain unknown until verified.
