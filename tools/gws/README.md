# gws

## Capability Summary
Pinned Google Workspace CLI integration for LiNKskills.

- Source of truth fork: `https://github.com/linktrend/link-gws-cli`
- Vendored snapshot: `tools/gws/vendor/link-gws-cli`
- Runtime binary pin/checksum policy: `tools/gws/pin.json`

`tools/gws/bin/gws` enforces strict runtime pinning:
1. Select platform artifact from pin metadata.
2. Verify release archive SHA256 before install.
3. Verify binary checksum/version after install.
4. Fail hard on any mismatch.

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `tools/gws/bin/gws --version`
- `tools/gws/bin/gws drive files list --params '{"pageSize": 5}'`
- `tools/gws/bin/gws gmail +send --to user@example.com --subject "Hello" --body "Test"`
- `tools/gws/bin/gws calendar +agenda --today`

## Pin/Sync Strategy
See `tools/gws/PINNING.md` for the fork sync + pin bump workflow.
If any platform checksum is temporarily unavailable, it is listed in `pin.json` under `sync.missing_binary_checksum_targets` and runtime install will fail on that platform until resolved.
