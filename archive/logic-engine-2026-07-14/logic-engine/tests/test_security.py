from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
import uuid
from pathlib import Path

import sys

from fastapi.testclient import TestClient

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from logic_engine.api import create_app  # noqa: E402
from logic_engine.security import (
    TokenError,
    hash_api_key,
    issue_disclosure_token,
    validate_disclosure_token,
)  # noqa: E402


INTERNAL_TENANT = "00000000-0000-0000-0000-000000000001"
# codeql[py/clear-text-storage-sensitive-data]: Test-only ephemeral key fixture.
API_KEY = f"security-test-key-{uuid.uuid4().hex}"
PRINCIPAL = "linktrend-internal-agent"


class DisclosureTokenTests(unittest.TestCase):
    def test_issue_and_validate(self) -> None:
        token, claims = issue_disclosure_token(
            secret="secret",
            tenant_id="tenant-a",
            run_id="run-1",
            capability_id="lead-engineer",
            version="1.0.0",
            step_scope="phase.execute",
            ttl_seconds=120,
        )
        validated = validate_disclosure_token(token, "secret")
        self.assertEqual(validated.run_id, claims.run_id)
        self.assertEqual(validated.capability_id, "lead-engineer")

    def test_expired_token_rejected(self) -> None:
        token, _ = issue_disclosure_token(
            secret="secret",
            tenant_id="tenant-a",
            run_id="run-1",
            capability_id="lead-engineer",
            version="1.0.0",
            step_scope="phase.execute",
            ttl_seconds=1,
        )
        time.sleep(2)
        with self.assertRaises(TokenError):
            validate_disclosure_token(token, "secret")


class ProductionSecretFailClosedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.service_root = Path(__file__).resolve().parents[1]
        self.tmpdir = tempfile.TemporaryDirectory(prefix="logic-engine-security-")
        self.data_path = Path(self.tmpdir.name) / "store.json"
        self.catalog_path = Path(self.tmpdir.name) / "catalog.json"
        self.api_keys_path = Path(self.tmpdir.name) / "api_keys.json"
        self.gsm_secret_file = Path(self.tmpdir.name) / "missing-gsm.json"

        self.api_keys_path.write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "key_id": "primary",
                            "key_hash": hash_api_key(API_KEY),
                            "tenant_id": INTERNAL_TENANT,
                            "principal_id": PRINCIPAL,
                            "state": "active",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        os.environ["LOGIC_ENGINE_REPO_ROOT"] = str(self.repo_root)
        os.environ["LOGIC_ENGINE_DATA_PATH"] = str(self.data_path)
        os.environ["LOGIC_ENGINE_CATALOG_PATH"] = str(self.catalog_path)
        os.environ["LOGIC_ENGINE_PACKAGES_PATH"] = str(self.service_root / "config" / "packages.json")
        os.environ["LOGIC_ENGINE_API_KEYS_PATH"] = str(self.api_keys_path)
        os.environ["LOGIC_ENGINE_DPR_REGISTRY_PATH"] = str(self.service_root / "config" / "dpr_registry.json")
        os.environ["LOGIC_ENGINE_COMPLEXITY_PATH"] = str(self.service_root / "config" / "complexity_multipliers.json")
        os.environ["LOGIC_ENGINE_PROVIDER_PRICING_PATH"] = str(self.service_root / "config" / "provider_pricing.json")
        os.environ["LOGIC_ENGINE_CAPABILITY_POLICY_PATH"] = str(self.service_root / "config" / "capability_policy.json")
        os.environ["LOGIC_ENGINE_GSM_SECRET_FILE"] = str(self.gsm_secret_file)
        os.environ["LOGIC_ENGINE_ENV"] = "production"
        os.environ["LOGIC_ENGINE_SECRET_PROVIDER"] = "gsm"
        os.environ["LOGIC_ENGINE_ALLOW_NONPROD_SECRET_FALLBACK"] = "false"

        self.client = TestClient(create_app())
        self.headers = {"Authorization": f"Bearer {API_KEY}"}

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_execution_fails_closed_and_enters_safe_mode(self) -> None:
        create = self.client.post(
            "/v1/runs",
            json={
                "tenant_id": INTERNAL_TENANT,
                "principal_id": PRINCIPAL,
                "idempotency_key": "prod-fail-closed",
                "capability_id": "lead-engineer",
                "input_payload": {},
                "mode": "MANAGED",
                "origin": "INTERNAL",
                "billing_track": "track_1",
                "venture_id": "venture-alpha",
            },
            headers=self.headers,
        )
        self.assertEqual(create.status_code, 503)

        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertTrue(health.json()["safe_mode"]["enabled"])


if __name__ == "__main__":
    unittest.main()
