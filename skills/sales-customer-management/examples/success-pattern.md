# Safe success example

Input uses only synthetic data:

```json
{"request_id":"scm-demo-001","workflow":"qualification","privacy_classification":"synthetic","authority":{"status":"confirmed","owner":"founder-demo","approved_actions":["prepare"]},"source_evidence":[{"ref":"fixture:lead-demo-001","claim":"Synthetic lead reports a need matching the declared segment.","status":"confirmed","provenance":"fixture","licence":"internal-synthetic"}]}
```

The result is `COMPLETED` for a qualification preparation, with a `qualified` or `needs-evidence` disposition, the fixture reference, `send: false`, `applied: false`, `mutated_records: false`, and next actions for the owner. No Odoo call or customer message occurs.
