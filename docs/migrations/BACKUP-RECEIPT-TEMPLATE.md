# Backup receipt template — stage/prod shared Supabase

**Owner:** LiNKplatform (live DB control plane)
**Skills role:** consume a filled receipt before any stage readiness claim that depends on applied migrations
**Rule:** Do **not** invent receipt fields. Leave blanks until Platform supplies real values.

Use one receipt per backup job. Attach the filled copy under Platform-owned evidence (or a Platform-supplied immutable ref). LiNKskills stage packets may **cite** the receipt path/ref; they must not fabricate timestamps, dump IDs, or restore proofs.

---

## Receipt header

| Field | Value |
|---|---|
| Receipt ID | `_PLATFORM_SUPPLIED_` |
| Environment | `stage` / `prod` (circle one; do not invent) |
| Project / DB identity | `_PLATFORM_SUPPLIED_` (Supabase project ref or internal DB ID) |
| Schema scope | `platform` + `lskills` (+ note any co-tenant schemas) |
| Backup operator | Platform role / human / job name |
| Skills commit pin (SQL package) | `_SKILLS_COMMIT_SHA_` |
| Platform commit pin (apply tooling) | `_PLATFORM_COMMIT_SHA_` |
| Manifest path | `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md` (in Skills pin) |

---

## Pre-apply backup

| Field | Value |
|---|---|
| Backup started (UTC) | `_PLATFORM_SUPPLIED_` |
| Backup completed (UTC) | `_PLATFORM_SUPPLIED_` |
| Backup method | logical dump / PITR snapshot / provider backup (Platform chooses) |
| Artifact location | `_PLATFORM_SUPPLIED_` (URI or GSM-ref; never paste secrets) |
| Artifact checksum (SHA-256) | `_PLATFORM_SUPPLIED_` |
| Retention until (UTC) | `_PLATFORM_SUPPLIED_` |
| Includes roles / grants | yes / no |
| Includes RLS policies | yes / no |

**Hard blocker if blank:** stage apply must not proceed without a completed pre-apply backup row.

---

## Restore dry-run (required before first live apply of a package)

| Field | Value |
|---|---|
| Restore target | disposable / non-shared clone only |
| Restore started (UTC) | `_PLATFORM_SUPPLIED_` |
| Restore completed (UTC) | `_PLATFORM_SUPPLIED_` |
| Verification query set | cite Platform verification SQL + Skills manifest verification block |
| Verification result | pass / fail |
| Evidence path | `_PLATFORM_SUPPLIED_` |

**Hard blocker if restore dry-run absent or failed.**

---

## Post-apply checkpoint (after Platform apply)

| Field | Value |
|---|---|
| Apply receipt ID | `_PLATFORM_SUPPLIED_` (separate apply receipt; link here) |
| Post-apply backup ID | `_PLATFORM_SUPPLIED_` (optional but recommended) |
| Schema verification UTC | `_PLATFORM_SUPPLIED_` |
| `lskills` tables present | list or evidence ref |
| RLS enabled on registry + review_queue | yes / no + evidence |
| Catalog count gate | `_PLATFORM_SUPPLIED_` (expected ≥ prior seed floor) |

---

## Explicit non-claims

- A filled **local** ephemeral Postgres proof is **not** a backup receipt.
- Skills agents must **not** create dumps from stage/prod credentials.
- Empty `_PLATFORM_SUPPLIED_` fields mean **blocked**, not “assumed OK”.
