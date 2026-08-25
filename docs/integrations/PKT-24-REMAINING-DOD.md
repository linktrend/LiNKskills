# PKT-24 remaining-DoD packaging lane

**State:** `PREPARATORY_ONLY` / `HOLD`

The earlier [`PKT-24-PRE-VPS-PREP.md`](./PKT-24-PRE-VPS-PREP.md) remains the
authoritative integration handoff. This bounded lane adds source-owned package
guards and offline rehearsal inputs for the later PKT-24 execution owner; it
does not regenerate the catalogue, change product documentation, apply a
migration, configure a consumer, contact a provider, deploy, activate, or
qualify anything.

## Package contents

- `configs/pkt24/consumer.local-test.example.json` is a loopback-only fixture.
  It has no live endpoint, credential, activation, or provider-contact path.
- `configs/pkt24/consumer.stage.reference.json` is a placeholder contract for
  a future owner. It deliberately keeps `live_enabled` and `activation_allowed`
  false and does not invent Platform URLs or credentials.
- `evidence/governed-skill-expansion/pkt24/fixtures/local-gateway.json` contains
  synthetic, redacted responses and stable event IDs for disconnect, bounded
  retry, and idempotent replay rehearsal.
- `pkt24_rehearsal.py` verifies the source migration manifest and down-file
  relationships, rejects unsafe local fixtures, and binds a preparatory receipt
  to an explicit Git ref, commit, tree, package digests, and changed paths.
- `pkt24-receipt.template.json` is intentionally unbound. A generated receipt
  must retain `PREPARATORY_ONLY`, `admission.admissible=false`, all claims false,
  and explicit PKT-22/23 and external proof holds.

## Migration and rollback boundary

The manifest covers the ordered source SQL bytes through migration `000012` and
records companion down files where they exist. Hash validation proves only that
the checked-out source bytes match the package; it is not an apply receipt.

LiNKplatform alone owns backup, restore rehearsal, role/RLS checks, apply, and
forward-fix or rollback. Migration `000012` remains blocked on the PKT-03/ISS-03
dependency. For a source-only rollback, revert the single checkpoint and rerun
the focused checks; never rewrite an immutable release or run destructive SQL
from LiNKskills.

## Offline rehearsal contract

The local fixture may be used only with a loopback fake Gateway. The executing
owner must demonstrate missing/invalid configuration refusal, read-only exact
release discovery, bounded retry after disconnect, redacted buffering, stable
event IDs, idempotent replay, and no activation or pointer mutation. Any result
is `LOCAL_ONLY`; it cannot clear provider, Platform, consumer, stage, VPS, E2E,
production, or qualification gates.

## Receipt binding and holds

Receipt identity is read from the physical checkout using an explicit full Git
ref. `HEAD`, copied merge-ref identities, dirty checkouts, mismatched tree
digests, or changed paths outside this package are not admissible inputs. The
receipt binder never substitutes an identity and never changes a false claim to
true. PKT-22, PKT-23, Platform, OpenClaw, LiNKautowork, VPS/deployment, and
independent-verification evidence remain separate unresolved proof classes.
