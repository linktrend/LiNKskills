# Advanced: canary-echo

- Keep business/shared side effects empty: packaged `text-echo` is `side_effect_class: none`.
- Allowed tool writes (`write_file`, etc.) are only inside the ephemeral sealed eval workspace;
  they must not touch the repository tree or shared stage/host state.
- Append-only `execution_ledger.jsonl` telemetry is mandatory and is not a certification claim.
- Prefer sealed Linux `bwrap` (or privileged Docker Linux with `bwrap`) for certifying runs.
- Never treat macOS `unproven` isolation receipts as promotion evidence.
- Local non-promoting sealed canaries (`--local-non-promoting`) must not write
  `evidence/phase10/sealed/` release artifacts or promote `usable`.

