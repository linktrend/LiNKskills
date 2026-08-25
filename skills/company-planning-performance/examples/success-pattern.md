# Success pattern

Input: a synthetic quarterly plan with two evidence-linked objectives, a KPI
with target 100, forecast 90, actual 84, unit `accounts`, precision `whole`,
and a supplied late signal.

Output: a `READY_FOR_OWNER` review that keeps the quarterly horizon explicit,
reports forecast and actual separately, calculates the evidence-backed
variance `-6`, preserves the late signal, and emits empty effects. The review
does not create a task or update a Program.
