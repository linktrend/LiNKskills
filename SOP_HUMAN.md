# SOP_HUMAN

Non-technical appliance manual for operating the LiNKskills Library.

## Index
1. Introduction
2. Department Functions
3. Daily Operation Checklist
4. Maintenance & Troubleshooting

## 1. Introduction
LiNKskills is a managed operating system of AI skills and tools.
- You request outcomes (reports, campaigns, audits, schedules).
- The system runs standardized workflows with checkpoints and logs.
- Each output is auditable and can be resumed if interrupted.

### What You Need To Know
- Skills = operating playbooks.
- Tools = command wrappers that execute actions.
- The system tracks state automatically and can resume paused work.

### Google CLI Routing (Launch Standard)
- Workspace actions must use `gws`.
- Non-Workspace Google and non-Google actions must use `ltr`.
- Routing source of truth: `configs/service_ownership.json`.

## 2. Department Functions

### Engineering
- Builds and delivers product capabilities.
- Key skills:
  - `lead-engineer`
  - `software-pm`
  - `persistent-qa`
  - `devops-sre`

### Growth
- Converts product goals into demand generation.
- Key skills/tools:
  - `marketing-strategist`
  - `seo-semantic-auditor`
  - `ad-intel`
  - `channel-ops`

### Operations
- Runs daily execution, governance, and reporting.
- Key skills:
  - `department-head`
  - `studio-health-reporting`
  - `executive-sync-8am`
  - `smart-file-clerk`

### Finance
- Produces GAAP reports and reconciles money movement.
- Key skills:
  - `revenue-adapter-base`
  - `studio-controller`
- Core finance template:
  - `shared/templates/MASTER_FINANCE_TEMPLATES.md`

## 3. Daily Operation Checklist
1. Confirm secrets are available (`LSL_MASTER_KEY` and required Vault entries).
2. Run or request scheduled workflows.
3. Review morning briefing output.
4. Review blockers and approvals.
5. Run validation before major updates.

## 4. Maintenance & Troubleshooting

### Common Error: `Secure Environment Required`
- Meaning: master key is missing.
- Fix:
  1. Set `LSL_MASTER_KEY` in your shell.
  2. Re-run the command.

### Common Error: `PENDING_APPROVAL`
- Meaning: workflow paused due to risk or missing context.
- Fix:
  1. Open the requested fields in the task output.
  2. Provide confirmation or missing data.
  3. Resume task.

### Common Error: `403` from external providers
- Meaning: token scope or permission mismatch.
- Fix:
  1. Refresh credentials/token in local environment.
  2. Re-authenticate tool access.
  3. Retry action.

### Common Error: Missing output sections (e.g., no Financial Health)
- Meaning: output contract not satisfied.
- Fix:
  1. Re-run with required contract fields.
  2. Ensure source inputs include all mandatory sections.

### Common Error: Validator failure
- Meaning: one or more skills/tools are non-compliant.
- Fix:
  1. Run `python3 validator.py --repo-root . --scan-all`.
  2. Read errors and patch exact files.
  3. Re-run until pass.
