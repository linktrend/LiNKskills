# Advanced Execution Logic

## Complex Branching & Edge Cases

### Scenario A: Skill with Complex Dependencies
- **Context**: User requests a skill that requires multiple MCP servers and custom scripts.
- **Logic**: 
  - Validate all dependencies exist before scaffolding.
  - Generate comprehensive `dependencies` array in frontmatter.
  - Create placeholder documentation in `references/api-specs.md` for each dependency.
  - If dependency validation fails, stop and request user to install/configure dependencies first.

### Scenario B: Skill Name Conflicts
- **Context**: User requests a skill name that conflicts with an existing folder (e.g., "skills/skill-template").
- **Logic**:
  - Check for exact name match first.
  - If conflict found, propose alternatives: `{name}-v2`, `{name}-custom`, or ask user for new name.
  - Do not proceed until conflict resolved.

### Scenario C: Custom Decision Tree Requirements
- **Context**: User specifies complex domain logic that requires custom Decision Tree steps.
- **Logic**:
  - Analyze the tools and use case to determine required Decision Tree checks.
  - Generate domain-specific checks (e.g., API key validation for API-based skills, file existence for file-processing skills).
  - Ensure all Decision Tree steps follow the fail-fast pattern.

## Performance Optimization
- **Batch File Creation**: When creating multiple template files, read all templates once and cache them in memory before writing.
- **Parallel Validation**: After scaffolding, run validator.py asynchronously if possible, but wait for results before Phase 5.
- **Template Caching**: Cache `skills/skill-template/` file contents in state.jsonl/flat-file slices to avoid re-reading on resume.

## Alternative Heuristics

### Pro Mode: Custom Template Variants
- For advanced users, allow specification of template variant (e.g., "minimal", "full", "api-focused").
- Each variant includes/excludes specific sections based on use case.

### Admin Mode: Override Validation
- Allow `--skip-validation` flag for rapid prototyping (with warning that skill may not be production-ready).
- Still generate all files, but skip Phase 4 validation step.
