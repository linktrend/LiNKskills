# Fictional success pattern

## Request

Fictional five-row register has one blank risk, one unknown next date, two stale records and one closed case. Report denominators, exclude closed case only if scope says active, and avoid treating blank risk/date as low/no deadline.

## Expected draft behavior

- Produce only `portfolio_rollup, upcoming_date_table, anomaly_register, scope_and_method` using the task schema.
- Link assertions to supplied sources; separate fact, inference, user report and legal authority.
- Keep unresolved issues visible and route to counsel/owner.
- Set `external_effects` and `mutations` to empty arrays.

This example is fictional and is not legal guidance, a real matter record, or an executed behavior result.
