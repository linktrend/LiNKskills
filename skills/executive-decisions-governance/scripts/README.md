# Offline helper

`helper_tool.py` accepts one JSON request from stdin or `--input` and prints a
deterministic JSON review artifact. It never calls a connector, sends a message,
activates a rule, creates a task, schedules a meeting, mutates a Program, or
writes outside stdout. Use synthetic, redacted, or public fixtures only.
