# Script disposition

No upstream script is copied, adopted, executed, or required. All source script locations are inventory-only. This method uses native session data and supplied evidence.

Original entrypoint filenames are preserved as `source_path` in the manifest; quarantined copies use `SKILL.source.md` so library discovery cannot treat them as active skills. Byte content and hashes are unchanged.
