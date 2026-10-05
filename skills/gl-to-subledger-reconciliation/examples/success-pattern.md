# Synthetic GL-to-subledger workpaper

- Entity/account/period: Entity A / AP control / 2026-09 / USD
- GL source control total: 18,000
- Subledger invoice rows: 10,000 + 4,000 + 4,000 = 18,000
- Two document references match; one 4,000 GL credit has no subledger reference.
- Result: aggregate totals tie, but the missing-side line remains an exception. No cause or journal entry is asserted.
