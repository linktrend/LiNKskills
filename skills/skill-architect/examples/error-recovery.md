# Example Trace: Error Recovery

## Scenario
A tool call fails during scaffolding due to a permission error or missing parameter, triggering the escalation protocol.

## Trace
**User**: "Create a data-analyzer skill with pandas and numpy tools."

**Thought**:
<thinking>
The user wants to create a data-analyzer skill. I'll extract the requirements and start scaffolding.
</thinking>

**Action**: Extract spec: `{name: "data-analyzer", description: "...", tools: ["pandas", "numpy"], ...}`
**Result**: Spec extracted successfully

**Action**: `make_dir(path="data-analyzer/advanced")`
**Result**: `ERROR: Permission denied - cannot create directory`

**Thought**:
<thinking>
The make_dir call failed with a permission error. According to the **Escalation Protocol** in `SKILL.md`, I must report the error and request user intervention. I should also check if the directory already exists or if there's a path issue.
</thinking>

**Action**: `list_dir(path=".")`
**Result**: `[...]` (directory listing shows no data-analyzer folder)

**Thought**:
<thinking>
The directory doesn't exist, so this is a genuine permission error. I'll report this to the user and suggest checking filesystem permissions or trying a different location.
</thinking>

**Response**: Error encountered during scaffolding: Permission denied when creating `data-analyzer/advanced` directory. 

**Escalation**: Please verify:
1. Write permissions for the repository root directory
2. Disk space availability
3. No conflicting processes locking the directory

Once resolved, I can resume from the directory creation step using the existing task_id.

**Action**: `write_file(path=".workdir/tasks/{{task_id}}/state.jsonl", contents={..., status: "SCAFFOLDING_FAILED", error: "Permission denied"})`
**Result**: State saved for resumption

**Thought**:
<thinking>
After user resolves the permission issue, I can resume from Phase 3 and continue scaffolding.
</thinking>

**User**: "Permissions fixed, please continue."

**Action**: Resume from Phase 3 using saved state
**Action**: `make_dir(path="data-analyzer/advanced")`
**Result**: `SUCCESS: Directory created`

**Action**: Continue with remaining scaffolding steps...
**Result**: Skill scaffolded successfully

**Response**: Successfully recovered from the permission error and completed scaffolding of the `data-analyzer` skill. The skill structure has been created and validated.
