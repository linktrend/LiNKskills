# Quarantined scripts

No upstream scripts were copied or executed. The source entrypoint copy under `references/upstream/` is data-only and is not executable.

Original entrypoint filenames are preserved as `source_path` in the manifest; quarantined copies use `SKILL.source.md` so library discovery cannot treat them as active skills. Byte content and hashes are unchanged.
