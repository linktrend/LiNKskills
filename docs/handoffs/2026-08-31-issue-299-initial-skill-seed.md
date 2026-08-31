# Issue 299 initial skill seed handoff

**Date:** 2026-08-31

**Branch:** `issue/299-admit-qualify-and-prepare-activation-routing-for`

**Source checkpoint:** `d3682ea993573609b3c0ac53fc3af43851b7bf2b`

## Completed

- Preserved exact, commit-bound source for Impeccable, Taste, Emil Kowalski,
  Awesome Design Skills, and the IDE Development Matt Pocock plus gstack
  hybrid.
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
- A non-promoting real certification run returned `suite_not_executable` for
  all five new adapters. This is the correct fail-closed outcome because their
  current evaluations do not execute consumer agents.
- The repository-wide secret scan found no finding in any new path. Its overall
  result remained blocked because the pre-existing synthetic-fixture declaration
  is bound to the prior candidate tree and becomes stale after any tree change.

## Remaining gates

1. Add real, consumer-profile agent execution to the established Eval Runner;
   prompt-only or suite-authored output cannot qualify these skills.
2. Run the qualifying cases on the sealed Linux executor with an external
   issuer key and digest-pinned image.
3. Publish exact eligible releases only for members that pass.
4. Let IDE Development, LiNKdeveloper, LiNKsites, and Google Workspace
   consumers independently enable the exact eligible releases and prove use.

No consumer activation, protected integration, staging promotion, or production
claim is authorized by this handoff.
