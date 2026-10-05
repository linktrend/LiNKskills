# Fictional task: mutual product-evaluation NDA review

This worked case demonstrates clause-level NDA review, source text analysis, a scope-trap review, and bounded draft edits. The input field names follow `references/schemas.json#/definitions/input`. The parties, agreement, and terms are invented. This is an issue-spotting example, not legal advice, a playbook position, or approval to sign.

## Input

```json
{
  "task_id": "20261005-0930-NDA-000001",
  "request_ref": "synthetic:nda-review-request-01",
  "source_refs": ["synthetic:mutual-evaluation-nda-v1"],
  "data_classification": "synthetic",
  "task_inputs": {
    "agreement_ref": "synthetic:mutual-evaluation-nda-v1",
    "party_roles": ["Northwind Devices: discloser and recipient", "Pinecone Metrics: discloser and recipient"],
    "transaction_context": "The parties are considering a six-week integration pilot and expect to exchange product documentation and test data.",
    "governing_law_text": null,
    "requested_analysis": "Review the supplied excerpt for confidentiality obligations, operational burden, and terms that go beyond confidentiality. Prepare proposed and fallback edits for counsel review.",
    "approved_playbook_ref": null,
    "amendments_and_schedules": []
  }
}
```

## Agreement facts and scope

- The supplied draft is described as mutual; each party may disclose and receive information during a product-evaluation pilot.
- Only Sections 2, 3, 6, 8, and 12 were supplied. No schedules, playbook, governing-law clause, or signature page was supplied.
- Section 3 limits use to evaluating the pilot, but Section 6 makes confidentiality obligations last seven years for all information.
- Section 8 assigns a party's developments conceived during discussions to the other party, whether or not based on the other party's confidential information. This is an IP-transfer provision, not only a confidentiality obligation.
- The supplied text does not establish enforceability, a governing jurisdiction, party authority, or an approved negotiation position.

## Clause findings

| Section | Text summary | Finding | Playbook status | Risk rationale / owner |
|---|---|---|---|---|
| 2 | Information disclosed in any form is confidential whether marked or not. | The definition has no marking or reasonable-identification limit in the excerpt. Consider whether the operational burden matches the parties' information flows. | not_provided | Business/legal review needed to choose a workable scope; no legal conclusion is made. |
| 3 | Use is limited to evaluating the integration pilot; disclosure to personnel and advisers is permitted if they are bound by written confidentiality duties. | Purpose is tied to the stated pilot. The excerpt does not say whether affiliates or service providers are included; do not assume they are. | not_provided | Deal owner should confirm who needs access to run the pilot. |
| 6 | Confidentiality lasts seven years after disclosure for every category of information. | The clause applies one duration to all information and the supplied text does not distinguish trade secrets. Its stated starting event is each disclosure; do not report that explicit event as missing. | not_provided | The requested duration and treatment of trade secrets are business/counsel choices; no universal term is asserted. |
| 8 | Each party assigns the other all developments conceived during discussions, whether or not derived from confidential information. | Broad present-tense assignment reaches work that may be unrelated to protected information. It is a separate IP allocation and exceeds a confidentiality-only NDA. | not_provided | Route the IP allocation to counsel and the product owner; no ownership conclusion is made. |
| 12 | No governing law or forum appears in the supplied excerpt. | The full agreement may contain an omitted term; jurisdiction is unknown on this record. | not_provided | Ask for the complete agreement before giving jurisdiction-dependent analysis. |

## Proposed draft edits for counsel review

**Section 2 — definition. Preferred:** “Confidential Information means non-public information disclosed by or on behalf of a party for the Evaluation Purpose that is marked confidential or that a reasonable recipient would understand to be confidential from its nature and the circumstances of disclosure.”

**Fallback:** Keep unmarked coverage only for information identified as confidential at disclosure and confirmed in writing within `[30]` days. The parties must select the confirmation period; the bracket is unresolved.

**Section 6 — duration. Preferred:** “The confidentiality and use obligations continue for `[three]` years from each disclosure; information qualifying as a trade secret remains protected only for as long as it remains a trade secret under applicable law.”

**Fallback:** Use a single finite period selected by the parties for all information. Retain the stated each-disclosure starting event unless the parties expressly choose a different one. These options are negotiation drafts, not a statement of market standard or enforceability.

**Section 8 — IP assignment. Preferred:** Delete the assignment and replace it with: “No ownership of either party's pre-existing or independently developed intellectual property transfers under this Agreement. Any pilot deliverable or license must be addressed in a separate written agreement signed by both parties.”

**Fallback:** Limit any later IP transfer to a specifically identified deliverable, with ownership, background IP, license, and consideration terms handled in a separate signed pilot agreement. The product owner and counsel should define the deliverable before drafting that instrument.

## Open questions and next owner

1. Please provide the complete agreement and any referenced schedule so Sections 2, 3, 6, 8, and 12 can be checked against definitions and cross-references.
2. Which governing law/forum and approved negotiation playbook apply, if any?
3. Which affiliates, service providers, or other representatives need access for the pilot?

Commercial counsel reviews the proposed wording and any law-dependent conclusion. The product owner decides whether Section 8 is needed for a separate pilot deliverable. Nothing in this example authorizes negotiation, signature, or external transmission.

## Contract-shaped summary

The structured form below is a compact instance of `references/schemas.json#/definitions/output`; the preceding text is the readable clause analysis.

```json
{
  "task_id": "20261005-0930-NDA-000001",
  "status": "completed_draft",
  "artifact_ref": null,
  "evidence_refs": ["synthetic:mutual-evaluation-nda-v1#section-2", "synthetic:mutual-evaluation-nda-v1#section-3", "synthetic:mutual-evaluation-nda-v1#section-6", "synthetic:mutual-evaluation-nda-v1#section-8", "synthetic:mutual-evaluation-nda-v1#section-12"],
  "open_questions": ["Provide the complete agreement and referenced schedules.", "Identify governing law/forum and any approved negotiation playbook.", "Confirm which representatives need access for the pilot."],
  "review_owner_role": "commercial counsel and product owner",
  "external_effects": [],
  "mutations": [],
  "work_product": {
    "agreement_facts": ["The supplied draft is described as mutual and covers a six-week product-evaluation pilot.", "Only Sections 2, 3, 6, 8, and 12 were supplied; no playbook or governing-law clause was provided."],
    "scope_traps": [{"section": "8", "obligation": "Assign all developments conceived during discussions, whether or not based on confidential information.", "why_out_of_nda_scope": "This transfers intellectual-property rights beyond protecting confidential information and should be evaluated separately."}],
    "clause_findings": [
      {"section": "2", "finding": "The supplied definition covers all disclosed information without a marking or reasonable-identification limit.", "playbook_status": "not_provided", "risk_rationale": "The scope may be difficult to administer; the record supplies no company position or jurisdiction-specific authority.", "source_quote_or_summary": "Confidential information includes information disclosed in any form whether marked or not."},
      {"section": "6", "finding": "A seven-year period from each disclosure applies to every information category, without distinct trade-secret treatment.", "playbook_status": "not_provided", "risk_rationale": "The appropriate duration is a party/counsel decision; enforceability is not assessed.", "source_quote_or_summary": "Confidentiality lasts seven years after disclosure for all information."}
    ],
    "proposed_redlines": [{"section": "8", "preferred_language": "No intellectual-property ownership transfers under this Agreement. Any evaluation deliverable or license will be addressed in a separate written agreement signed by both parties.", "fallback": "Limit a later transfer to a specifically identified deliverable and address background IP, ownership, license, and consideration in a separate signed agreement.", "objective": "Keep confidentiality obligations separate from project IP ownership.", "bracketed_unknowns": ["Identify any intended pilot deliverable before drafting a separate IP agreement."]}],
    "jurisdiction_gaps": ["The complete agreement and governing-law/forum language were not supplied; no enforceability conclusion is made."],
    "counsel_questions": ["Should Section 8 be removed from the NDA and handled in a separate pilot agreement?", "What duration and definition scope match the parties' negotiated position?"]
  }
}
```
