# Agent Workforce Management helper

`helper_tool.py` is a deterministic local normalizer. It reads JSON from stdin
or `--input`, emits one JSON owner-review envelope, and never calls a connector,
activates an agent, grants capability, copies credentials/private memory, or
mutates external state.

The new bounded source-review helper branch uses the existing LiNKskills Python environment with `jsonschema`. If that dependency is unavailable, stop and report the runtime gap; do not install packages or access the network automatically. This source contract is not proof of a native consumer execution route.
