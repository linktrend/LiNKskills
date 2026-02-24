# LiNKskills Global Tools Registry

This directory is the centralized CLI-first registry used by skills.

Layout:
- `/tools/[tool-name]/README.md`
- `/tools/[tool-name]/interface.json`
- `/tools/[tool-name]/bin/`
- `/tools/[tool-name]/test/`

Policy:
- Skills must prioritize tools from this registry.
- If a tool is missing, use `/skills/tool-architect` to design and register it.
