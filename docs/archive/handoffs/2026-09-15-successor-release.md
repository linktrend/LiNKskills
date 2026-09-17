# LiNKskills successor release — issue 372

Authority: Portfolio Successor Launch Authorization v1 and its revised Definition
of Done, approved at successor launch. Source, live operation and ordinary founder
configuration remain distinct. No worker agents are dispatched by this successor.

## Source reconciliation

Protected development at entry: `53a715278bbf333375774be4a9301fb5ba7e9667`,
tree `810ddcfa2a41e501c8a38379f7fc44199991a38a`.
Issue 372 retains accepted issues 363, 359, 365, 361 and 367 through issue 367
`c82d2ae35e7080077473178ae1ce90103c8ab787`; issues 370 and 371 through issue 371
`ffae16a5dd24cc70ed88078a7590fa2d5eb89d7b`. None was an ancestor of protected
development at entry. The obsolete issue-371-only PR exception is removed from
the combined candidate; its original commit remains preserved.

## Remaining production binding completed in this checkpoint

- HTTP and MCP production startup share a Postgres registry/receipt adapter.
- Every request rechecks the Platform-issued runtime binding against the
  Platform-owned enabled consumer binding and exact release allowlist.
- Registry manifests and resource bytes are digest checked; revocation is read
  afresh. Runtime cannot modify publication or activation rows.
- Use and feedback receipts are durable, idempotent and isolated by actor/org.
  Writes invoke the existing PACI write verification/introspection path.
- Production readiness includes v2 store and published catalogue availability.
- Sealed execution qualification precedes consumer activation. Pending actor
  configuration is still reported separately and is never claimed as live use.
- A separate qualify/export and publish command seals the complete package with
  the existing external evaluator issuer. Publication does not activate consumers.
- GitHub Actions builds the exact runtime/evaluator images, checks the new
  PostgreSQL behavior, retains SBOM/vulnerability output and artifact checksums.

## Server01 handoff contract

Owner: Server01 Production Owner, task `01a0a309-7dfd-7a52-8764-2ebd7fa25be4`.
Platform #284 is excluded by the owner's current runtime readback.
Do not deploy this document alone: wait for the accepted commit/tree, protected
integration receipt and successful hosted artifact identity.

1. Retrieve `linkskills-server01-<exact commit>` directly from GitHub Actions to
   Server01. Verify archive checksums and image labels against `source.json`.
   Retain or produce an existing-authority detached signature for the exact image
   or archive before release acceptance; a checksum is not a signature.
2. Retain the prior working image/configuration and a recoverable database backup.
3. Apply the additive migration after isolated validation:
   `supabase/migrations/20260915031801_lskills_provider_v2_runtime.sql`, SHA-256
   `1262ad8200130d7127407d659fc0d9ddfdc5aacba164aab9fd8ad64ccdd914e1`.
   Prerequisites: existing lskills schema and runtime/librarian roles. No previous
   migration is rewritten. Verify runtime SELECT-only publication/binding grants,
   actor/org receipt RLS, duplicate replay and conflicting-payload rejection.
4. Run the evaluator image with no network and without privileged Docker. Inject
   the existing `LINKTREND_SKILLS_PROD_EVAL_RUNNER_ISSUER_KEY` through the approved
   process environment route, plus immutable SecretRef/version/issuer identity,
   and `LINKSKILLS_SEALED_CERT_IMAGE=<exact evaluator tag>@sha256:<digest>`.
   Bubblewrap must actually deny case networking; inability to isolate remains a
   technical failure. Never use the workstation privileged certification script.
   Command: `qualify --package /tmp/linkskills-hosted-sealed/package.json` with a
   bounded writable evidence mount. Retain the five-case-group evidence and seal.
5. Publish the verified package using the publisher-only database credential in
   `LINKSKILLS_PUBLISHER_DATABASE_URL`, the issuer environment and command
   `python3 /opt/linkskills/scripts/provider_release.py publish --package <path>
   --expected-commit <accepted image source commit>`.
6. Provision an explicit private canary binding in `lskills.provider_bindings`
   for verified PACI org, actor and runtime-binding identifiers, profile
   `cursor-macos`, and the five exact release IDs. Ordinary consumer configuration
   remains separate; no global Cursor/Codex/OpenClaw mutation is implied.
7. Deploy the exact runtime image with existing Postgres/PACI secret references.
   Prove health/readiness, catalogue discovery, exact entrypoint/resource bytes,
   legacy denial, one safe local procedure, use report/status, restart persistence,
   isolated backup restore and prior-release rollback. Return redacted receipts.

## Validation and outstanding work

Local lightweight checks: 15 focused tests passed, 1 hosted DB test skipped,
4 execution tests deselected; 27 existing deploy/HTTP/MCP contract tests passed.
Python syntax, YAML parsing and diff whitespace passed. Secret scan is repeated
against the staged checkpoint before push. No local Docker, dependency install
or heavy build was used.

Hosted checks, final security/identity review, protected integration, immutable
artifact signing, qualification/publication and live acceptance are outstanding.
This checkpoint is not DONE or a live acceptance receipt. The local packager's
first attempt failed disk-full before branch/PR publication; no protected ref
changed. The host resource rule forbids local containers/builds and preserves
all existing worktrees and user data.

Recovery for the additive tables: revert the application/configuration to its
retained release; preserve new tables and qualification evidence. Do not drop
state as a rollback. Disable the private canary binding independently. Publisher
may revoke new releases through the lifecycle column without changing bytes.
