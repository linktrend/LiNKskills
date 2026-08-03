# Success Pattern

Scenario: certify the stage lifecycle canary with a deterministic echo.

1. Agent loads `canary-echo` and resolves packaged `text-echo` 1.0.0.
2. Agent runs `text-echo HELLO_CANARY` and receives the exact token.
3. Eval Runner seals an executor receipt with `network_isolation=denied`.
4. Certifier promotes only when sealed receipts validate.
