# Company communication helper

`helper_tool.py` is a deterministic local validator/extractor for a communication draft. It reads a JSON file and prints JSON only. It never sends a message, calls an external service, chooses transport, writes a ledger, or mutates a product system.

Examples:

```bash
python3 scripts/helper_tool.py --input draft.json --mode validate
python3 scripts/helper_tool.py --input draft.json --mode extract
```
