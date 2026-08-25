# Offline helper

`helper_tool.py` accepts a synthetic JSON object or path and emits a deterministic legal-operations preparation summary. It redacts/rejects restricted-looking input, preserves only evidence references, marks jurisdiction uncertainty, and keeps sign/accept/send/file/mutate effects false.

```bash
python3 skills/commercial-contracts-legal-operations/scripts/helper_tool.py \
  --input '{"workflow":"plain_language_summary","matter_ref":"matter-demo-001","jurisdiction":"unknown","privacy_classification":"synthetic","source_evidence":[{"ref":"fixture:source-demo-001","status":"confirmed"}]}'
```

The helper is not legal advice, a direct API, an MCP server, an e-signature client, a document store, or a legal-system connector. Human lawyer/Principal review remains required.
