# Offline helper

`helper_tool.py` accepts one JSON request from stdin or `--input` and prints a
deterministic JSON result. It does not call a network, calendar, image store,
health service, messaging system, or private destination, and it does not
write outside stdout. Use it for synthetic fixtures or redacted snapshots only.
