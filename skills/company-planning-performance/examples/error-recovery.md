# Error recovery

If actual evidence is absent, return `DRAFT` with `NOT_COMPARABLE` and a clear
uncertainty entry. If a caller requests activation, scheduling, sending,
credential access, or Program/Task mutation, return `BLOCKED` with typed
uncertainty and empty effects. Never repeat private or confidential input in
the error response.
