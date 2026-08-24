# Governed Browser Use helper

`helper_tool.py` is an offline deterministic classifier. It accepts one JSON
request on stdin and emits one schema-shaped JSON decision on stdout. It never
opens a browser, performs network I/O, reads credentials, writes a download,
or mutates a consumer system.

Example:

```bash
printf '%s' '{"task_id":"demo","target":"https://example.com","requested_action":"public_read","content_trust":"public_page","brain_rules":[]}' | python3 scripts/helper_tool.py
```
