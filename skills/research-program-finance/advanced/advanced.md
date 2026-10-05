# Period, funding, and formula details

## Status model

Each monetary row has period, currency, value type, source, and state: `actual`, `committed`, `budget`, `forecast`, or `proposed`. Do not aggregate these states into one unlabeled total. Keep award ceiling, cash received, restricted balance, open commitments, and unrestricted cash as separate fields when sources expose them.

## Indirect calculation representation

When a current award-specific source provides a rate and base, display the formula as `eligible base × cited rate = arithmetic result`. Record the cited source, effective dates, base definition, exclusions, and owner confirmation. If any input is absent, do not calculate that row as settled. Never import numerical values or exclusion thresholds from the upstream sample template.

## Burn and milestone cash

For each period, show actual cash spend separately from budgeted and forecast outflow. If actual history is missing, state that actual burn is unavailable. A scenario may project cash only from an explicit opening balance, receipt schedule, spending assumptions, and timing conventions; label it a scenario, not a fact. Compare period-specific cash availability with milestone cash needs; a timing gap is an exception for owner review, not a program decision.

## Decision-owner boundary

Send cost classification, allowability, capitalization, rate application, and accounting framework questions to Sara/controller with the exact record and missing facts. Technical milestone definitions go to Eric/program technical owner. Jane can format evidence and track the review queue only.
