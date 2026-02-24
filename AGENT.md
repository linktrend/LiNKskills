# System Conventions: Skill Registry

## Project Identity
You are an expert operator in a Venture Studio environment. Your capabilities are extended via the modular skills found in this directory.

## Execution Protocol
1. **Always Check the Ledger**: Before starting, check `execution_ledger.jsonl` for pending tasks.
2. **Persistence First**: Use the `.workdir/tasks/` directory for any task spanning more than one turn.
3. **Registry Layout**: Skills reside in `/skills`. Tools reside in `/tools`.
4. **Automation-Only Repository Operations**: Use `/scripts/lsl-update.sh` for save/push, `/scripts/lsl-review.py` for branch validation/merge review, and `/scripts/lsl-deploy.sh` for deployment. Direct manual git workflows are disallowed except break-glass recovery.
5. **Manifest and Activation Control**: Keep `/manifest.json` and `/configs/activation.json` aligned; runtime capability activation must come from `active_uid_list`.
6. **Tool Priority**: Skills must prioritize global `/tools`. If a tool is missing, use `tool-architect` to create it first.
7. **Google Workspace Standard**: Use `/tools/gw/bin/gw` as the primary interface for Gmail, Drive, Docs, Sheets, Calendar, and Chat operations, replacing individual ad-hoc scripts.
8. **Web Automation Standard**: Use `/tools/playwright-cli/bin/pw-cli` for stateless/background Playwright operations (`install`, `screenshot`, `pdf`, `codegen`) and `/tools/fast-playwright/bin/start-mcp` for interactive session-based browsing with accessibility snapshots.
9. **Strict Adherence**: Follow the **Decision Tree** in each `SKILL.md` verbatim.
10. **Intelligence Floor**: Verify that runtime capability satisfies `engine.min_reasoning_tier` and `engine.context_required` before execution.
11. **CLI-First Tooling**: Use native CLI first, then wrapper scripts; direct APIs and MCP require explicit protocol conditions.
12. **Learning Loop**: After every completion or failure, review `./references/old-patterns.md` and update it whenever a new reusable lesson is identified.

## Formatting
- Use ISO 8601 dates in Taipei time.
- All JSON artifacts must adhere to the schemas in `./references/schemas.json`.
