# Issue 299 initial skill seed handoff

**Date:** 2026-08-31

**Branch:** `issue/299-admit-qualify-and-prepare-activation-routing-for`

**Current evidence source checkpoint:** `d507a656ae110eca7eb67eb6d165c6c40bb39035`

## Completed

- Preserved exact, commit-bound source for Impeccable, Taste, Emil Kowalski,
  and Awesome Design Skills.
- Began the previously intended migration of the existing Principal-created
  LiNKtrend hybrid from IDE Development. The hybrid was not newly assembled by
  this issue; its adapted gstack and Matt Pocock components were preserved
  byte-for-byte from protected IDE Development source.
- Added five fail-closed collection inventories containing 112 member releases.
- Added five LiNKskills-native family adapters with non-overlapping routing.
- Preserved upstream licence and notice texts.
- Namespaced collection members, including `awesome-impeccable`, so a preset
  cannot collide with the official Impeccable family.
- Kept every new release unqualified, ineligible, and inactive by default.
- Regenerated the catalog from the immutable source checkpoint.

The existing Google Workspace collection remains governed by its existing 95
unqualified, ineligible member releases. It was not bypassed or relabelled by
this intake.

## Validation evidence

- Six initial-seed collection, digest, namespace, and routing tests passed.
- Fifteen existing Google Workspace, provider-contract, and role-pack tests
  passed.
- All five adapter validations passed.
- The complete registry scan passed across 75 targets, with only pre-existing
  warnings.
- Catalog generation and provenance check passed at 56 catalog skills and zero
  usable skills.
- Added a confined `skill_script` Eval Runner adapter that stages an immutable
  skill release, rejects unsafe paths and symlinks, and emits execution receipts.
- The hybrid adapter's executable routing-conformance suite passed all 22 cases
  in the sealed Linux executor with network isolation denied, 22 execution
  receipts, and a weighted score of 1.0. The non-promoting run correctly forced
  `eval_pending`, wrote no sealed release evidence, and performed no catalog or
  ledger promotion. This adapter result does not qualify the 19 members.
- Repaired the confined executor's Linux handling of container Python symlinks;
  it now binds the governed executable directory instead of attempting a
  redundant Bubblewrap mount onto a symlink destination.
- Non-promoting runs for the four design-family adapters returned
  `suite_not_executable`. This is the correct fail-closed outcome because their
  current evaluations do not execute consumer agents.
- The repository-wide secret scan found no finding in any new path. Its overall
  result remained blocked because the pre-existing synthetic-fixture declaration
  is bound to the prior candidate tree and becomes stale after any tree change.

## Remaining gates

1. Add real, consumer-profile agent execution for the four design adapters and
   each underlying hybrid member; adapter routing conformance alone cannot
   qualify content.
2. Run the qualifying cases on the sealed Linux executor with an external
   issuer key and digest-pinned image.
3. Publish exact eligible releases only for members that pass.
4. Let IDE Development, LiNKdeveloper, LiNKsites, and Google Workspace
   consumers independently enable the exact eligible releases and prove use.

No consumer activation, protected integration, staging promotion, or production
claim is authorized by this handoff.

IDE Development's physical hybrid copy remains the rollback source until the
LiNKskills releases are qualified, pinned, consumer-proven, and safe to cut
over. Its removal is not authorized by this checkpoint.

## Approved initial-canary admission completion

The Principal subsequently approved the lean initial-seed route: make the
source members compliant, classify and admit suitable members for internal
canary use, publish immutable adapter bundles through the existing LiNKskills
publisher, and leave behavioral improvement to real consumer use. The proposed
temporary consumer evaluation harness was rejected and was not built.

- Audited all 207 source members across the six collections.
- Approved 204 for internal canary use, blocked two Taste members pending
  correction, and marked the backward-compatibility Taste v1 member
  superseded. No exact duplicate or already-retired source member was found.
- Kept all 207 global eligibility decisions `ineligible`: consumer activation,
  ordinary selectability, and tool authority remain false.
- Added per-route admission gates to all six family adapters. A blocked member
  returns `NOT_ELIGIBLE` without disclosing a source entrypoint.
- Added the missing `google-workspace-operations` adapter over all 95 preserved
  Google Workspace members.
- Produced disabled, consumer-owned exact activation manifests for IDE
  Development, LiNKdeveloper, LiNKsites, and Google Workspace.
- Registered six immutable canary adapter bundles using the existing SQLite
  publisher path. This is a local canary publication receipt, not a live VPS,
  current-pointer, stable-qualification, or consumer-activation claim.

The next authorized work is outside LiNKskills: each consumer applies its exact
disabled manifest, activates only the routes and tool permissions it owns, and
returns real-use telemetry/evidence through the existing LiNKskills evaluation
loop. Stable qualification remains evidence-dependent.
