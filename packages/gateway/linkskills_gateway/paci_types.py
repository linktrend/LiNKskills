"""PACI envelope constants for LiNKskills Gateway (frozen consumer pin).

Pinned to Platform frozen ``platform.auth-token-envelope/0.1.0`` at Platform
HEAD ``0455846487d0b8c583859060ba8b4be70e7f0b48`` /
``@linktrend/platform-contracts@0.3.0``.

AuthClaims ``platform.auth-claims/1.1.0`` is unchanged. Historical claim-shape
package pin ``0.2.2`` remains valid for AuthClaims-only surfaces; PACI envelope
adoption uses contracts package ``0.3.0``.

**Evidence class:** local/fake conformance against frozen fixtures. Stage/prod
PACI issuer remains a Platform gate (not live-proven).
"""

from __future__ import annotations

# --- Envelope identity (frozen 0.1.0) ----------------------------------------

PACI_TOKEN_TYP = "paci+jwt"
PACI_ALG = "ES256"
PACI_CLAIMS_NAMESPACE = "https://linktrend.dev/claims/auth"

PACI_ENVELOPE_CONTRACT_ID = "platform.auth-token-envelope"
PACI_ENVELOPE_CONTRACT_VERSION = "0.1.0"
PACI_ENVELOPE_CONTRACT = f"{PACI_ENVELOPE_CONTRACT_ID}/{PACI_ENVELOPE_CONTRACT_VERSION}"

# PACI adoption package pin (envelope 0.1.0 + AuthClaims 1.1.0).
PLATFORM_CONTRACTS_PACKAGE_PACI = "0.3.0"
PLATFORM_HEAD_PACI = "0455846487d0b8c583859060ba8b4be70e7f0b48"

PACI_ENVELOPE_SCHEMA_BYTES_SHA256 = (
    "7173b9f9bca59ce8a0e3e3dc2b78b680dd07fdd2451215e3ecd97ff3dd463eed"
)
PACI_ENVELOPE_CONTENT_HASH = (
    "9335b1855c3b3a5ec01b40c18ea85a98826192cbfba3110e07399d896e890a12"
)

# Frozen AuthClaims dependency (unchanged by the envelope freeze).
AUTH_CLAIMS_CONTRACT_VERSION = "platform.auth-claims/1.1.0"
AUTH_CLAIMS_PACKAGE_HISTORICAL = "0.2.2"  # claim-shape only; PACI uses 0.3.0
AUTH_CLAIMS_PACKAGE = AUTH_CLAIMS_PACKAGE_HISTORICAL
AUTH_CLAIMS_SCHEMA_BYTES_SHA256 = (
    "c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1"
)
AUTH_CLAIMS_CONTENT_HASH = (
    "fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567"
)

# Phase-1 access-token lifetime bound (reject longer, including 3600).
MAX_ACCESS_TOKEN_TTL_SECONDS = 900

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
CLIENT_ASSERTION_LIFETIME_MAX_S = 300  # private_key_jwt assertion ≤ 5 minutes

# Loopback hosts permitted for HTTP only under LINKSKILLS_AUTH_MODE=local-test.
LOCAL_TEST_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

# Env names for SecretRef-backed private_key_jwt (introspection / client).
ENV_PACI_CLIENT_PRIVATE_KEY_FILE = "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE"
ENV_PACI_CLIENT_KID = "LINKSKILLS_PACI_CLIENT_KID"
ENV_AUTH_MODE = "LINKSKILLS_AUTH_MODE"
AUTH_MODE_LOCAL_TEST = "local-test"
AUTH_MODE_PRODUCTION = "production"

# Explicit local-test gate name for stub assertion signer (never production).
LOCAL_TEST_ASSERTION_SIGNER_GATE = "LINKSKILLS_AUTH_MODE=local-test"

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
