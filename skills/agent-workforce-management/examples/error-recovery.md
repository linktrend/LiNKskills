# Error recovery

If evidence is missing or marked `not_reported`, return `DRAFT` with the missing
reference in `uncertainty`. If a request asks to activate, suspend, retire,
approve a grant, or copy credentials/private memory, return `BLOCKED` with empty
workforce arrays. If a nested item is malformed, report only a typed reason and
do not echo the malformed content.
