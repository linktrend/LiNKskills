# Method-specific extension

## Applied method

1. Confirm source, access scope, schema, metric definitions, unit, timezone, and freshness; do not assume connector availability.
2. Profile the smallest relevant slice first: rows, columns, types, nulls, keys, ranges, and duplicate/grain checks.
3. Translate the question into a clear metric and population; document joins, filters, aggregation grain, and exclusions.
4. Use read-only queries for analysis; inspect the query plan or cost only when relevant and available.
5. Reconcile totals against known controls or source context; separate computed values from interpretations.
6. Report query/results, data quality and metadata gaps, and alternative explanations; do not turn correlation into cause.

## Focused support: SQL dialect and query safety

Before composing SQL, identify the actual engine and version from supplied metadata or an approved read-only connection. If the dialect is unknown, use only syntax supported by the supplied interface or mark the query as a draft requiring dialect review. Check engine-specific identifier quoting, date/time arithmetic, timezone conversion, null handling, JSON access, and pagination rather than guessing from another warehouse.

Use explicit columns, bounded date/row ranges, and parameterized values where the interface supports them. Keep analysis queries read-only; do not execute DDL/DML, stored procedures, file export, or unbounded scans. Inspect a query plan or cost estimate only when available and authorized. Record the source table, grain, joins, filters, units, and freshness with the result. A syntactically plausible query is not evidence that its semantics match the business metric.

## Scope guard

Use only authorized, already available data and read-only operations. No new API, account, connector, or paid service.

If the requested method cannot be completed with available evidence or tools, return a bounded partial deliverable and name the precise gap. Do not replace a missing input with an invented value.
