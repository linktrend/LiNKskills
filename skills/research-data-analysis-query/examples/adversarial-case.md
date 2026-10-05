# Focused adversarial fixture

## Input

A CSV has one row per line item, repeated order IDs, null refunds, and ambiguous “revenue” columns; the user asks for monthly revenue.

## Expected behavior

Inspect grain and definitions, distinguish gross/net/refund treatment, avoid summing duplicated order-level amounts, state unresolved choices, and provide a query/calculation only once the definition is clear or explicitly assumed.

This is an authored evaluation fixture, not an observed model output or PASS receipt.
