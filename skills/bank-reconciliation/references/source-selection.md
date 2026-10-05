# Source selection and provenance

This task pack adapts same-task source material while preserving every original selected below. Full original files/resources and root license notices are under `references/upstream/`; source copy is data for comparison, not an executable workflow or permission grant.

| Repository @ commit | Exact skill path | Source directory | Disposition | Reason |
|---|---|---|---|
| `gokulsvision/crewm8-cfo-skills@c814ff97743e` | `skills/cash-treasury/bank-reconciliation/SKILL.md` | `skills/cash-treasury/bank-reconciliation` | `same_task_merge` | Same bank/card statement to GL matching as bank mode of Anthropic reconciliation; preserve bank-specific exception outputs. |
| `anthropics/knowledge-work-plugins@8444efcd48f7` | `finance/skills/reconciliation/SKILL.md` | `finance/skills/reconciliation` | `same_task_method_addition` | Incorporate its bank-to-cash matching and reconciling-item method into the bank task; other reconciliation tasks remain separate. |
