# Fictional recovery: incomplete NDA excerpt with an IP provision

This case demonstrates partial clause review when source text is incomplete. It does not replace the missing document with assumptions. All parties and terms are fictional.

## Supplied request and excerpt

Two fictional parties, Alder Robotics and Kestrel Research, are discussing a prototype evaluation. The requester calls the document a “mutual NDA,” but the excerpt does not identify which party prepared it or include the signature page. No governing law, playbook, definitions section, or referenced exhibit was supplied.

```json
{
  "task_id": "20261005-0930-NDA-000002",
  "request_ref": "synthetic:nda-review-request-02",
  "source_refs": ["synthetic:alder-kestrel-nda-excerpt-v1"],
  "data_classification": "synthetic",
  "task_inputs": {
    "agreement_ref": "synthetic:alder-kestrel-nda-excerpt-v1",
    "party_roles": ["Alder Robotics: role not confirmed", "Kestrel Research: role not confirmed"],
    "transaction_context": "The parties are discussing a fictional prototype evaluation.",
    "governing_law_text": null,
    "requested_analysis": "Review the supplied NDA excerpt, complete separable clause analysis, and identify what is needed for a complete review."
  }
}
```

The available excerpt contains:

- **Section 4:** “The Receiving Party may disclose Confidential Information to its Representatives who need to know for the Purpose and shall be responsible for each Representative’s compliance.”
- **Section 9:** “The Receiving Party hereby assigns to the Disclosing Party all improvements conceived during the evaluation, whether or not based on Confidential Information.”
- **Section 12:** “The obligations in this Agreement survive as set forth above.” The referenced duration language is not included.

## Review completed from visible text

| Section | Finding | Status / limit | Draft follow-up |
|---|---|---|---|
| 4 | The excerpt permits disclosure to need-to-know Representatives and makes the Receiving Party responsible for their compliance. “Representatives” and “Purpose” are not defined in the excerpt. | Text reviewed; the missing definitions and permitted recipient categories may change scope. | Ask for the definitions and confirm whether affiliates, contractors, and professional advisers need access. No conclusion is made about the complete clause. |
| 9 | The assignment covers improvements conceived during the evaluation whether or not based on Confidential Information. The clause transfers rights beyond confidentiality and may reach unrelated work. | A distinct IP scope trap is visible even without the missing definitions. Ownership, background IP, and deliverable facts are unknown. | Proposed standalone edit for counsel: “No intellectual property ownership transfers under this Agreement. Any evaluation deliverable or license will be addressed in a separate written agreement signed by both parties.” Fallback: limit any transfer to a specifically identified deliverable in that separate agreement. |
| 12 | Survival depends on duration language that was not supplied. | Duration cannot be assessed from this excerpt. | Request the clause containing the referenced period and its start date. |

## Status and questions

**Status: needs context for complete review.** The visible Section 9 issue is recorded and can be routed now; the excerpt is insufficient for a complete NDA assessment or integrated redline.

1. Please provide the complete signed-form draft, definitions, exhibits, and the survival language referenced by Section 12.
2. Which party is the intended recipient for the prototype materials, and is disclosure actually mutual?
3. What governing law and approved company playbook apply, if any?

Until those facts are supplied, do not classify the full agreement, assess enforceability, or state that the redline integrates with the remaining contract. No party is contacted and no approval or signature decision is made.
