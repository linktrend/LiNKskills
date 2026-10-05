# Fictional worked example

The following synthetic example demonstrates the output shape only. It is not a real analysis, evaluated fixture, or evidence of runtime behavior.

```json
{
  "status": "partial",
  "scope": {
    "as_of": "2025-06-30T16:00:00Z",
    "universe_version": "demo-universe-v1",
    "snapshot": "fictional-bars-2025Q2-r3"
  },
  "checks": {
    "availability": "unknown",
    "key_uniqueness": "pass",
    "join_cardinality": "fail",
    "coverage": {
      "expected_sessions": 20,
      "observed_sessions": 19,
      "unit": "sessions"
    },
    "missingness": {
      "null_rows": 1,
      "reason": "vendor record absent",
      "mechanism": "unknown"
    },
    "revision_lineage": {
      "amendment_known_at": "2025-07-08T12:00:00Z",
      "safe_for_2025-06-30_decision": false
    },
    "survivorship": {
      "delisted_entity_rows_retained": true,
      "terminal_proceeds": "unknown"
    },
    "leakage": {
      "transform_fit_scope": "full_sample",
      "finding": "unsafe; fold-local fit required"
    }
  },
  "exceptions": [
    "Join increased 19 rows to 23; one-to-many cause unresolved."
  ],
  "sensitivity": [
    "Dropping the affected entity changes descriptive coverage from 95% to 90%; no performance estimate computed."
  ],
  "counterevidence": [
    "Source history may contain a pre-close snapshot not supplied."
  ],
  "proposed_repairs": [
    "Rebuild the join with validated key and preserve source rows."
  ],
  "limitations": [
    "Fictional worked example; no real data inspected."
  ],
  "owner_handoffs": [
    "Eric: implement only after approved data contract."
  ],
  "gaps": [
    "Source snapshot/version or as-of evidence is incomplete; point-in-time safety remains unknown."
  ]
}
```
