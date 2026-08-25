# Offline helper

`helper_tool.py` accepts a synthetic JSON object or a path to one and emits a deterministic preparation summary. It only hashes the supplied request, preserves evidence references, rejects restricted/live-looking input, and sets every external effect to false.

```bash
python3 skills/sales-customer-management/scripts/helper_tool.py \
  --input '{"workflow":"qualification","privacy_classification":"synthetic","source_evidence":[{"ref":"fixture:lead-demo-001","status":"confirmed"}]}'
```

The helper is deliberately not an Odoo connector, native CLI, direct API client, MCP server, or transport adapter. The owning consumer must provide any capability receipt and approval separately.
