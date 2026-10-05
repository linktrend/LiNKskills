# Fictional worked example

The following synthetic example demonstrates the output shape only. It is not a real analysis, evaluated fixture, or evidence of runtime behavior.

```json
{
  "status": "partial",
  "identity": {
    "issuer": "Fictional Co.",
    "cik": null,
    "as_of": "2025-07-10T00:00:00Z",
    "cik_status": "unknown",
    "cik_reason": "No verified identifier was supplied in this fictional partial fixture."
  },
  "filing_timeline": [
    {
      "form": "S-3",
      "accepted": "2025-06-01T15:00:00Z",
      "interpretation": "registered capacity only",
      "accession": "fictional-a1"
    },
    {
      "form": "424B",
      "accepted": null,
      "interpretation": "not supplied; no active takedown conclusion",
      "accession": "fictional-a2"
    }
  ],
  "facts": [
    {
      "name": "shares_outstanding",
      "value": 1000000,
      "unit": "shares",
      "period": "2025-06-30",
      "context": "cover page",
      "known_at": "2025-07-08",
      "source": "fictional filing p.1"
    }
  ],
  "ownership_reconciliation": [],
  "offering_state": "capacity_only",
  "dilution_calculation": {
    "status": "not_calculated",
    "reason": "no executed issuance numerator/date"
  },
  "xbrl_fallback": {
    "status": "not_needed",
    "text_source": null
  },
  "conflicts": [],
  "limitations": [
    "Fictional evidence. Filing form not legal advice."
  ],
  "owner_handoffs": [
    "Sara: legal/accounting conclusion if requested."
  ],
  "gaps": [
    "Required source evidence is incomplete; dependent conclusions remain partial."
  ]
}
```
