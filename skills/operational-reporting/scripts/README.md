# Operational reporting helper

`helper_tool.py` validates a local JSON report input and emits a deterministic
JSON summary. It does not query a calendar, mailbox, battery, health system, or
agent; it does not send or mutate anything.

```bash
python3 scripts/helper_tool.py --input report.json --mode validate
python3 scripts/helper_tool.py --input report.json --mode render-no-change
```
