#!/usr/bin/env python3
"""Stage gateway config schema + fail-closed selection (Lane A, reference-only)."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_ROOT = REPO_ROOT / "packages" / "contracts"
STAGE_CONFIG_DIR = REPO_ROOT / "configs" / "stage"
STAGE_DOC = REPO_ROOT / "docs" / "stage" / "PACI-GATEWAY-STAGE-GATE.md"
SCHEMA_NAME = "stage-gateway-config-v0.1.json"
PLATFORM_CANDIDATE = "421a35e97bc302be0f5e1f196d0a5e8d132f6fd8"
PLACEHOLDER_RE = re.compile(r"^_(PLATFORM_SUPPLIED_|SECRETREF_RENDERED_).+")

sys.path.insert(0, str(CONTRACTS_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages" / "client"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))

from linkskills_contracts import load_schema, validate_instance  # noqa: E402
from linkskills_client.paci_token_client import (  # noqa: E402
    AUTH_MODE_LOCAL_TEST,
    AUTH_MODE_PRODUCTION,
    PaciConfigError,
    require_https_outside_local_test,
)
from linkskills_gateway.auth import resolve_auth_mode  # noqa: E402
from linkskills_gateway.jwks import assert_https_transport  # noqa: E402
from linkskills_gateway.auth import AuthError  # noqa: E402


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise TypeError(f"expected object root: {path}")
    return data


def _is_platform_placeholder(value: str) -> bool:
    text = value.strip()
    return bool(PLACEHOLDER_RE.match(text)) or text.startswith("REPLACE_WITH_")


def assert_stage_selection_rules(config: Mapping[str, Any]) -> list[str]:
    """Return human-readable violations of Lane A fail-closed stage selection."""
    errors: list[str] = []
    target = str(config.get("deployment_target") or "")
    auth_mode = str(config.get("auth_mode") or "")
    linkskills_env = str(config.get("linkskills_env") or "").strip().lower()

    if target in {"stage", "canary", "production"} and auth_mode == AUTH_MODE_LOCAL_TEST:
        errors.append(
            f"auth_mode=local-test forbidden for deployment_target={target!r}"
        )
    if target in {"stage", "canary", "production"} and auth_mode != AUTH_MODE_PRODUCTION:
        errors.append(
            f"auth_mode must be production for deployment_target={target!r} "
            f"(got {auth_mode!r})"
        )
    if target in {"stage", "canary"} and linkskills_env not in {
        "stage",
        "staging",
        "production",
        "prod",
    }:
        errors.append(
            f"linkskills_env must be production-like for {target!r} "
            f"(got {linkskills_env!r})"
        )

    machine = config.get("machine_token") or {}
    if machine.get("private_key_material") != "secretref_file_path_only":
        errors.append("private_key_material must be secretref_file_path_only")
    if machine.get("token_endpoint_auth_method") != "private_key_jwt":
        errors.append("token_endpoint_auth_method must be private_key_jwt")

    paci = config.get("paci") or {}
    key_file = str(paci.get("client_private_key_file") or "")
    if "BEGIN" in key_file.upper() and "PRIVATE" in key_file.upper():
        errors.append("inline PEM private key material forbidden in stage config")
    if "\n" in key_file:
        errors.append("client_private_key_file must be a single SecretRef path")

    pins = config.get("platform_pins") or {}
    if pins.get("certified_candidate_is_live_paci_authority") is not False:
        errors.append("certified_candidate_is_live_paci_authority must be false")
    if pins.get("certified_platform_candidate_sha") != PLATFORM_CANDIDATE:
        errors.append("certified_platform_candidate_sha pin mismatch")

    blockers = config.get("hard_blockers") or []
    blocker_ids = {str(b.get("id") or "") for b in blockers if isinstance(b, dict)}
    if "platform-stage-paci-issuer-absent" not in blocker_ids and target in {
        "stage",
        "canary",
    }:
        # Valid reference configs must still surface the issuer-absent blocker
        # while Platform has not published a live stage issuer.
        issuer = str(paci.get("issuer") or "")
        if _is_platform_placeholder(issuer) or not issuer:
            errors.append(
                "hard_blockers must include platform-stage-paci-issuer-absent "
                "while issuer remains Platform-supplied placeholder"
            )

    # Absolute https URLs (non-placeholder) must satisfy https outside local-test.
    if auth_mode != AUTH_MODE_LOCAL_TEST:
        url_fields = [
            ("gateway.gateway_url", (config.get("gateway") or {}).get("gateway_url")),
            ("paci.issuer", paci.get("issuer")),
            ("paci.jwks_uri", paci.get("jwks_uri")),
            ("paci.token_endpoint", paci.get("token_endpoint")),
            ("paci.introspection_url", paci.get("introspection_url")),
        ]
        for label, raw in url_fields:
            value = str(raw or "").strip()
            if not value or _is_platform_placeholder(value):
                continue
            parsed = urlparse(value)
            if parsed.scheme in {"http", "https"}:
                try:
                    require_https_outside_local_test(
                        value, auth_mode=auth_mode, label=label
                    )
                except PaciConfigError as exc:
                    errors.append(str(exc))
                try:
                    assert_https_transport(value, label=label, auth_mode=auth_mode)
                except AuthError as exc:
                    errors.append(str(exc.message))
    return errors


class StageGatewayConfigSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_schema(SCHEMA_NAME)
        cls.stage_ref = STAGE_CONFIG_DIR / "gateway-stage.reference.json"
        cls.canary_ref = STAGE_CONFIG_DIR / "gateway-canary.reference.json"
        cls.forbidden = STAGE_CONFIG_DIR / "gateway-stage.local-test.forbidden.json"

    def test_schema_loads_with_required_consts(self) -> None:
        self.assertEqual(
            self.schema["properties"]["schema_version"]["const"],
            "0.1",
        )
        auth = self.schema["properties"]["auth_mode"]
        self.assertEqual(auth["const"], "production")
        material = self.schema["properties"]["machine_token"]["properties"][
            "private_key_material"
        ]
        self.assertEqual(material["const"], "secretref_file_path_only")
        live = self.schema["properties"]["platform_pins"]["properties"][
            "certified_candidate_is_live_paci_authority"
        ]
        self.assertIs(live["const"], False)

    def test_stage_reference_validates(self) -> None:
        payload = _load_json(self.stage_ref)
        result = validate_instance(payload, SCHEMA_NAME)
        self.assertTrue(result.ok, msg=[str(e) for e in result.errors])
        self.assertEqual(assert_stage_selection_rules(payload), [])

    def test_canary_reference_validates(self) -> None:
        payload = _load_json(self.canary_ref)
        result = validate_instance(payload, SCHEMA_NAME)
        self.assertTrue(result.ok, msg=[str(e) for e in result.errors])
        self.assertEqual(assert_stage_selection_rules(payload), [])
        self.assertTrue((payload.get("gateway") or {}).get("canary_enabled"))

    def test_local_test_on_stage_fails_schema_and_selection(self) -> None:
        payload = _load_json(self.forbidden)
        result = validate_instance(payload, SCHEMA_NAME)
        self.assertFalse(result.ok)
        joined = " ".join(str(e) for e in result.errors)
        self.assertIn("auth_mode", joined)
        selection = assert_stage_selection_rules(payload)
        self.assertTrue(
            any("local-test" in err for err in selection),
            msg=selection,
        )

    def test_inline_pem_rejected_by_selection_rules(self) -> None:
        payload = _load_json(self.stage_ref)
        mutated = json.loads(json.dumps(payload))
        mutated["paci"]["client_private_key_file"] = (
            "-----BEGIN " "PRIVATE KEY-----\nMII\n-----END " "PRIVATE KEY-----"
        )
        errors = assert_stage_selection_rules(mutated)
        self.assertTrue(any("inline PEM" in e for e in errors), msg=errors)

    def test_http_url_outside_local_test_rejected(self) -> None:
        payload = _load_json(self.stage_ref)
        mutated = json.loads(json.dumps(payload))
        mutated["paci"]["issuer"] = "http://example.invalid"
        mutated["paci"]["jwks_uri"] = "http://example.invalid/.well-known/jwks.json"
        errors = assert_stage_selection_rules(mutated)
        self.assertTrue(any("https" in e.lower() for e in errors), msg=errors)

    def test_placeholders_are_not_invented_live_hosts(self) -> None:
        for path in (self.stage_ref, self.canary_ref):
            payload = _load_json(path)
            paci = payload["paci"]
            for key in ("issuer", "jwks_uri", "token_endpoint", "introspection_url"):
                self.assertTrue(
                    _is_platform_placeholder(str(paci[key])),
                    msg=f"{path.name} {key} must remain Platform placeholder",
                )
            self.assertTrue(
                _is_platform_placeholder(str(payload["gateway"]["gateway_url"]))
            )

    def test_hard_blocker_platform_stage_paci_issuer_absent(self) -> None:
        for path in (self.stage_ref, self.canary_ref):
            payload = _load_json(path)
            ids = {b["id"] for b in payload["hard_blockers"]}
            self.assertIn("platform-stage-paci-issuer-absent", ids)
            blocking = [
                b
                for b in payload["hard_blockers"]
                if b["id"] == "platform-stage-paci-issuer-absent"
            ]
            self.assertEqual(blocking[0]["status"], "blocking")

    def test_stage_gate_doc_exists_and_names_blockers(self) -> None:
        self.assertTrue(STAGE_DOC.is_file())
        text = STAGE_DOC.read_text(encoding="utf-8")
        self.assertIn("Platform stage PACI issuer absent", text)
        self.assertIn("certified Platform candidate ≠ live PACI authority", text)
        self.assertIn("LINKSKILLS_AUTH_MODE=local-test", text)
        self.assertIn("private_key_jwt", text)
        self.assertIn("SecretRef", text)
        self.assertIn(PLATFORM_CANDIDATE, text)

    def test_resolve_auth_mode_defaults_production_for_stage_env(self) -> None:
        # LINKSKILLS_ENV alone does not select local-test.
        mode = resolve_auth_mode(
            {"LINKSKILLS_ENV": "stage", "LINKSKILLS_AUTH_MODE": "production"}
        )
        self.assertEqual(mode, AUTH_MODE_PRODUCTION)
        mode_default = resolve_auth_mode({"LINKSKILLS_ENV": "stage"})
        self.assertEqual(mode_default, AUTH_MODE_PRODUCTION)


if __name__ == "__main__":
    unittest.main()
