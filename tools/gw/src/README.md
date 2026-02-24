# GW Engine Technical README

This directory contains the internalized Google Workspace gateway engine used by `/tools/gw/bin/gw`.

## Installation

Run from this directory:

```bash
cd tools/gw/src
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Identity Management

The gateway expects local OAuth identity files in this directory:

- `credentials.json`
- `token.json`

These files are machine-local and intentionally ignored by git to preserve account isolation.

## Service Architecture

Service adapters are implemented under `services/`:

- `gmail.py` (Gmail)
- `drive.py` (Drive)
- `docs.py` (Docs)
- `sheets.py` (Sheets)
- `calendar.py` (Calendar)
- `slides.py` (Slides)
- `chat.py` (Chat)
- `tasks.py` (Tasks)

Shared support modules live in `utils/`:

- `auth.py` (OAuth scopes and credential/token flow)
- `logging.py` (JSONL audit logger)

## CLI Usage

Call the engine directly:

```bash
python3 cli.py --version
python3 cli.py setup --config credentials.json
python3 cli.py gmail list --label INBOX --max-results 10
python3 cli.py drive list --page-size 10
python3 cli.py tasks list-lists
python3 cli.py tasks create --title "Follow up" --list-id @default
```

The registry wrapper delegates to this engine:

```bash
../bin/gw <service> <command> [options]
```

## Contribution Rules

When adding a new Google service:

1. Add a new service module in `services/`.
2. Import and wire it in `cli.py` (group, commands, handlers, audit flow).
3. Add required OAuth scope(s) in `utils/auth.py` (`GWAuth.SCOPES`).
4. Keep deterministic JSON outputs and error codes consistent with existing services.
