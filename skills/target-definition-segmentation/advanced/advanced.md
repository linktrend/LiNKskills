# Advanced Target Definition and Segmentation Guidance

## Input discipline

Use stable opaque references. Every material criterion and candidate or segment observation must point to supplied evidence. Evidence status `not_reported` forces `DRAFT`. Unknown is a result, not a request to infer or enrich data.

## Determinism

Normalize criteria in their supplied order. Normalize output items by stable reference. When prioritization requires a tie breaker, declare it before evaluation and use the lexical stable reference; never introduce a hidden model score. Duplicate references, undeclared criteria, unsupported operators, or conflicting evidence fail closed.

## Safety and refusal

Reject requests to select, activate, contact, publish, certify, enrich, infer protected or sensitive traits, invoke a connector, claim Program authority, claim live Platform use, or mutate LiNKtarget. Do not echo rejected private values. Outputs always carry empty `messages_sent`, `external_calls`, `selections`, and `mutations`.

## Ownership

The package owns only source instructions, schemas, fixtures, and deterministic tests. Population data, policy, grants, Program decisions, runtime adapters, publication, and LiNKtarget state remain external and unavailable here.
