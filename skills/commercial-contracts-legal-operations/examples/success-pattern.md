# Safe success example

Input is synthetic and source-bound:

```json
{"request_id":"clo-demo-001","workflow":"obligation_register","matter_ref":"matter-demo-001","jurisdiction":"not_reported","privacy_classification":"synthetic","privilege_status":"not_claimed","authority":{"status":"confirmed","owner":"principal-demo","approved_actions":["read","prepare"]},"source_evidence":[{"ref":"fixture:source-demo-001","claim":"Synthetic source states a notice obligation in section 4.","status":"confirmed","provenance":"fixture","licence":"internal-synthetic","source_kind":"owner_supplied"}]}
```

The result is a reviewable obligation row with the source reference, `jurisdiction_assessment.status: supplied_not_verified`, `legal_authority: not_granted`, and all effects false. It does not copy an instrument, schedule a deadline, send notice, or decide enforceability.
