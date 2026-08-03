# Canary Echo Specs

Request fields:
- `token` — exact string to echo
- `mode` — `plain` or `json`

Response fields:
- plain mode: echoed token on stdout
- json mode: `{"status":"ok","echo":"<token>"}`
