# Agent Workforce Management helper

`helper_tool.py` is a deterministic local normalizer. It reads JSON from stdin
or `--input`, emits one JSON owner-review envelope, and never calls a connector,
activates an agent, grants capability, copies credentials/private memory, or
mutates external state.
