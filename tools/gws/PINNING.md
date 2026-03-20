# gws Pinning and Upstream Sync Strategy

LiNKskills treats `link-gws-cli` as production source-of-truth.

## Pin Metadata
All runtime pin fields live in `tools/gws/pin.json`:
- `source.fork_url`
- `source.fork_commit`
- `runtime.release_tag`
- `runtime.artifacts[]` (per-platform archive checksum)
- `runtime.expected_binary_checksums[]` (per-platform binary checksum)
- `sync.last_sync_date`

## Runtime Contract
`tools/gws/bin/gws` must:
1. Resolve target platform.
2. Install from pinned release artifact list (`fork` URL first, fallback URLs optional).
3. Verify archive SHA256.
4. Verify extracted binary SHA256.
5. Verify `gws --version` matches pinned version.
6. Exit non-zero on any mismatch.
7. Exit non-zero when the target platform has no `expected_binary_checksums` entry.

## Periodic Sync Workflow
1. Fetch upstream `googleworkspace/cli` into fork.
2. Merge/rebase into fork integration branch.
3. Run LiNKskills compatibility gates.
4. Publish/update release artifacts for the fork tag.
5. Update `pin.json` (commit/tag/checksums/date).
6. Commit pin bump only after all gates pass.
