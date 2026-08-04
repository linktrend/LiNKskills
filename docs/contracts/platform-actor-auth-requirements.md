# Platform Actor / Auth Requirements (LiNKskills Consumer)

- **Status:** Requirements contract v0.1 (fake-backed until Identity gate passes)
- **Date:** 2026-07-27
- **Authority:** `docs/CURSOR-GROK-EXECUTION-PROMPT.md` + approved plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`
- **Plan refs:** §20.1, §8.2, §29.4 Identity gate
- **Related ADRs:** 0003, 0005, 0007

## 1. Authority split

| Concern | Owner |
|---|---|
| Actor identity, organisation membership, authentication, credential issuance/lifecycle, token format, issuer | **LiNKplatform** |
| Claims LiNKskills requires; acceptance/rejection behavior; claim-version compatibility; fixtures/fakes; domain bindings referencing platform actor ID | **LiNKskills** |

LiNKskills must not become a competing permanent actor registry or organisation-wide identity issuer.

## 2. Minimum claims LiNKskills requires

Authenticated platform claims must supply (names conceptual until Platform publishes exact schema):

| Claim | Required | Notes |
|---|---|---|
| `platform_actor_id` | Yes | Canonical stable ID; all Skills bindings reference this |
| `actor_kind` | Yes | e.g. human operator agent, service, Program executor |
| `organisation_id` / membership | Yes | Organisation context |
| `internal_status` | Yes | Internal vs non-internal as Platform defines |
| `allowed_service_scopes` | Yes | Must include the Skills scopes requested for the operation |
| `credential_id` | Yes | Identity of the presented credential |
| `expires_at` / rotation metadata | Yes | Reject expired / not-yet-valid |
| `claim_schema_version` | Yes | For compatibility gates |

Optional but recommended when available: session ID, runtime profile hint, Program/repository/Issue correlation IDs (opaque).

## 3. LiNKskills-derived binding fields

From claims + Skills bindings, resolve for a request:

- actor ID/kind;
- organization;
- runtime profile and adapter version;
- session/run correlation;
- Program/repository/Issue context where present;
- allowed LiNKskills operations.

## 4. Hard rejects (fail closed)

Reject (do not trust request-body identity) when:

- credentials missing, expired, or wrong audience/service;
- required claims absent or claim schema unsupported;
- requested Skills operation outside `allowed_service_scopes`;
- actor presents or requests Supabase service-role / Librarian credentials;
- caller attempts to self-assert a different `platform_actor_id` than the credential-derived ID.

## 5. Credential distribution rules

- Actors receive scoped short-lived credentials or approved OAuth/service identity only.
- Actors never receive Supabase service-role or Librarian credentials.
- Secrets remain in GSM; configs use names/placeholders only.
- TLS required for non-loopback access.

## 6. Conformance expectations

LiNKskills will publish fixtures that prove:

1. valid claim set → accepted; domain binding can be created/updated against `platform_actor_id`;
2. expired / wrong-scope / missing-claim → rejected with safe error text;
3. request-body actor spoofing ignored;
4. fake Platform issuer interchangeable with live issuer once Identity gate evidence exists.

Until LiNKplatform publishes the canonical contract, LiNKskills develops against fakes and **does not** declare live authentication complete (Identity gate).

## 7. Out of scope

- Permission-to-act for Program side effects (host/Program Ledger).
- Brain private-memory or conversation auth.
- Combined Brain/Skills credential.
