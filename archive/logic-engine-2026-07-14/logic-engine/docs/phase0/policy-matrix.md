# Policy Matrices (Phase 0-3)

## Trust Class Matrix
| Trust Class | Status | Notes |
| :--- | :--- | :--- |
| Class A (Controlled) | Active | Internal managed execution only |
| Class B (Uncontrolled self-hosted) | Deferred | Not implemented in this sprint |
| Class C (Public/third-party) | Deferred | Not implemented in this sprint |

## Disclosure Matrix
| Mode | Status | Notes |
| :--- | :--- | :--- |
| Managed server disclosure | Active | Token + run-scoped manifest for server-side execution |
| Client executable fragment disclosure | Deferred | No JIT in this sprint |

## Retention Matrix
| Artifact | Retention Class | TTL |
| :--- | :--- | :--- |
| Success execution payload | Metadata-only | No raw body stored |
| Failed/blocked diagnostics | Redacted diagnostics | 30 days |
| Disclosure events | Metadata | 180 days |
| Audit logs | Metadata | 180 days |

Purge cadence: daily retention worker.
