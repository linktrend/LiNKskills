# LTR Engine Technical README

This directory contains the internalized LiNKtrend Runtime engine used by `/tools/ltr/bin/ltr`.

## Installation

Run from this directory:

```bash
cd tools/ltr/src
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Identity Management

For OAuth-backed Google APIs in ltr lanes (Analytics/Ads/Search Console/YouTube), the runtime expects:

- `credentials.json`
- `token.json`

These files are machine-local and intentionally ignored by git.

## Service Architecture

Service adapters are implemented under `services/`.

Primary retained lanes:
- `analytics.py`
- `ads.py`
- `search_console.py`
- `youtube.py`
- `yt_analytics.py`
- `maps_routes.py`
- `news.py`
- `env_context.py`

Local support:
- `utils/auth.py`
- `utils/logging.py`

## CLI Usage

Call the engine directly:

```bash
python3 cli.py --version
python3 cli.py setup --config credentials.json
python3 cli.py analytics report --property-id 123 --start-date 2026-01-01 --end-date 2026-01-31 --metrics activeUsers
python3 cli.py news trending --limit 10
```

Registry wrapper:

```bash
../bin/ltr <service> <command> [options]
```

## Note on Workspace Services

Workspace service lanes were cut over to `gws` and are intentionally blocked in ltr with `SERVICE_MOVED_TO_GWS`.
