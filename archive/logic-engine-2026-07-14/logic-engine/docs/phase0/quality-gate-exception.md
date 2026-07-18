# Phase 0 Quality Gate Exception

## Validator Exception (Known)
`python3 validator.py --repo-root . --scan-all` currently reports missing `.workdir/tasks` directories under skill folders.

## Exception Scope
- This Phase 0-3 implementation does not modify skill frontmatter or golden anatomy.
- The current exception is documented and tracked as remediation backlog work.

## Remediation Constraint
- No remediation may involve changing `skills/*/SKILL.md` frontmatter.
- Remediation must be structural (directories, validation policy evolution, or non-frontmatter contract updates).
