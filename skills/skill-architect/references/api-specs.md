# API & Tool Technical Specifications

## External Endpoints
N/A - Skill Architect uses only local filesystem operations.

## Local Tool Internal Parameters

### `make_dir`
- **Purpose**: Create directory structure for new skill.
- **Parameters**: 
  - `path` (string, required): Full path to directory to create.
- **Behavior**: Creates parent directories if they don't exist.

### `write_file`
- **Purpose**: Write file content during scaffolding.
- **Parameters**:
  - `path` (string, required): Full path to file.
  - `contents` (string, required): File content to write.
- **Behavior**: Overwrites existing files. Creates parent directories if needed.

### `read_file`
- **Purpose**: Read template files from `skills/skill-template/` directory.
- **Parameters**:
  - `path` (string, required): Path to file to read.
- **Behavior**: Returns file contents as string.

### `list_dir`
- **Purpose**: Check for existing skill folders.
- **Parameters**:
  - `path` (string, required): Directory path to list.
- **Behavior**: Returns list of directory entries.

## Dependency Versions
- Python 3.8+: Required for `validator.py` execution.
- No external dependencies required.
