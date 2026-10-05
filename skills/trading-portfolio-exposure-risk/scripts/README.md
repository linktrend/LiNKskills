# Local structural helpers

`helper_tool.py` performs read-only JSON syntax checks for explicit package-local `.json` paths. It does not run strategies, validate JSON Schema, access providers, alter files or establish behavior qualification.

`validate_package.py` checks package headings, canonical draft metadata, JSON syntax, and the local file manifest. The local manifest excludes itself and `references/execution-profile.json` to avoid a circular content hash; the canonical profile carries its own identity hashes. Neither helper qualifies behavior or replaces the linkskills root validator.
