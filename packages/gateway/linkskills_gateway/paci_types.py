"""PACI envelope constants for LiNKskills Gateway (consumer adapter).

Pinned to Platform DRAFT ``platform.auth-token-envelope/0.1.3-draft``.

**Evidence class:** ``implemented but not proven against frozen Platform PACI
service`` — the Platform envelope remains DRAFT
(``platform.auth-token-envelope/0.1.3-draft``); AuthClaims 1.1.0 is frozen.
"""

from __future__ import annotations

# --- Envelope identity (DRAFT; not frozen) ---------------------------------

PACI_TOKEN_TYP = "paci+jwt"
PACI_ALG = "ES256"
PACI_CLAIMS_NAMESPACE = "https://linktrend.dev/claims/auth"

PACI_ENVELOPE_CONTRACT_ID = "platform.auth-token-envelope"
PACI_ENVELOPE_CONTRACT_VERSION = "0.1.3-draft"
PACI_ENVELOPE_CONTRACT = f"{PACI_ENVELOPE_CONTRACT_ID}/{PACI_ENVELOPE_CONTRACT_VERSION}"

# Frozen AuthClaims dependency (unchanged by the envelope draft).
AUTH_CLAIMS_CONTRACT_VERSION = "platform.auth-claims/1.1.0"
AUTH_CLAIMS_PACKAGE = "0.2.2"
AUTH_CLAIMS_SCHEMA_BYTES_SHA256 = (
    "c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1"
)
AUTH_CLAIMS_CONTENT_HASH = (
    "fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567"
)

# --- Algorithm / header hardening (RFC 8725) --------------------------------

FORBIDDEN_ALGS = frozenset(
    {
        "none",
        "None",
        "NONE",
        "HS256",
        "HS384",
        "HS512",
        "HS1",
    }
)
FORBIDDEN_HEADER_KEY_PARAMS = frozenset({"jwk", "jku", "x5u", "x5c"})
UNDERSTOOD_CRIT_HEADERS = frozenset({"alg", "typ", "kid"})

# --- JWKS / introspection bounds --------------------------------------------

JWKS_CACHE_TTL_SECONDS = 5 * 60  # ≤ 5 minutes
INTROSPECTION_CACHE_TTL_SECONDS = 30  # ≤ 30 seconds
CLOCK_SKEW_SECONDS = 0  # zero skew (AuthClaims + JWT NumericDate)

# --- Evidence class markers -------------------------------------------------

EVIDENCE_CLASS_FAKE_LOCAL = "fake_local"
EVIDENCE_CLASS_LIVE_STAGE = "live_stage"
EVIDENCE_CLASS_LIVE_PROD = "live_prod"
EVIDENCE_STATUS_NOT_PROVEN = (
    "implemented but not proven against frozen Platform PACI service"
)

# Prefer stdlib + cryptography for ES256. Do NOT add PyJWT/jose unless
# unavoidable — Skills Lane 1 uses cryptography 46.x directly.
CRYPTO_BACKEND = "cryptography"
CRYPTO_BACKEND_NOTE = (
    "ES256 verify via cryptography.hazmat (no PyJWT/jose dependency)."
)
