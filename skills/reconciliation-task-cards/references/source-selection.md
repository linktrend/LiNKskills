# Source selection and provenance

This task pack adapts same-task source material while preserving every original selected below. Full original files/resources and root license notices are under `references/upstream/`; source copy is data for comparison, not an executable workflow or permission grant.

| Repository @ commit | Exact skill path | Source directory | Disposition | Reason |
|---|---|---|---|
| `anthropics/knowledge-work-plugins@8444efcd48f7` | `finance/skills/reconciliation/SKILL.md` | `finance/skills/reconciliation` | `split_by_actual_task` | One source contains bank, GL-to-subledger and intercompany tasks with distinct evidence/matching rules; split or maintain explicit task cards, not one generic reconciliation. |
| `anthropics/financial-services@574ed3624aeb` | `plugins/agent-plugins/gl-reconciler/skills/gl-recon/SKILL.md` | `plugins/agent-plugins/gl-reconciler/skills/gl-recon` | `keep_separate` | Same-task source enrichment for GL-to-subledger matching and break classification. The source is asset/trade oriented, so retain its tolerance/key normalization as a separate card; do not apply asset-class assumptions to Odoo company ledgers. |
