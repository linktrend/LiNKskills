# Error Recovery Pattern

Scenario: isolation unavailable on the host.

1. Agent attempts confined execution; wrapper cannot stamp `denied`.
2. Runner refuses certification (or stamps `unproven` only under local-test escape hatch).
3. Catalog classification stays `draft` with machine-readable reason.
4. Operator re-runs via sealed Linux / privileged Docker `bwrap` path.
