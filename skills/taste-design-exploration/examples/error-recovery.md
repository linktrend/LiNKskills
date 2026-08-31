# Error recovery

If no route fits, return `NOT_APPLICABLE`. If two routes fit equally, return `AMBIGUOUS`. Missing source bytes, unsupported consumer profiles, or absent tool authority are blockers rather than reasons to select a substitute silently.
