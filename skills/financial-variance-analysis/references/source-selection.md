# Source selection and provenance

This task pack adapts same-task source material while preserving every original selected below. Full original files/resources and root license notices are under `references/upstream/`; source copy is data for comparison, not an executable workflow or permission grant.

| Repository @ commit | Exact skill path | Source directory | Disposition | Reason |
|---|---|---|---|
| `anthropics/knowledge-work-plugins@8444efcd48f7` | `finance/skills/variance-analysis/SKILL.md` | `finance/skills/variance-analysis` | `keep_separate` | Variance drivers, bridge and narrative are a separate analytical deliverable that may feed statements/budgets/board packs. |
| `anthropics/financial-services@574ed3624aeb` | `plugins/agent-plugins/month-end-closer/skills/variance-commentary/SKILL.md` | `plugins/agent-plugins/month-end-closer/skills/variance-commentary` | `same_task_merge` | Same task as variance-analysis: compute actual/prior/budget variances and source driver narrative. Preserve both source-specific materiality logic and report narrative as evaluation branches; no unsupported defaults. |
