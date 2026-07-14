from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import sys

from fastapi.testclient import TestClient

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from logic_engine.api import create_app  # noqa: E402
from logic_engine.config import load_settings  # noqa: E402
from logic_engine.engine import AuthContext, LogicEngine  # noqa: E402
from logic_engine.types import KillSwitchLevel, KillSwitchScopeType, RunCreateRequest  # noqa: E402


INTERNAL_TENANT = "00000000-0000-0000-0000-000000000001"
KEY_A = "key-a"
KEY_B = "key-b"
PRINCIPAL_A = "principal-a"
PRINCIPAL_B = "principal-b"


class PolicyControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.service_root = Path(__file__).resolve().parents[1]
        self.tmpdir = tempfile.TemporaryDirectory(prefix="logic-engine-policy-")
        self.data_path = Path(self.tmpdir.name) / "store.json"
        self.catalog_path = Path(self.tmpdir.name) / "catalog.json"
        self.api_keys_path = Path(self.tmpdir.name) / "api_keys.json"

        self.api_keys_path.write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "key_id": "a",
                            "api_key": KEY_A,
                            "tenant_id": INTERNAL_TENANT,
                            "principal_id": PRINCIPAL_A,
                            "state": "active",
                        },
                        {
                            "key_id": "b",
                            "api_key": KEY_B,
                            "tenant_id": INTERNAL_TENANT,
                            "principal_id": PRINCIPAL_B,
                            "state": "active",
                        },
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
        os.environ["LOGIC_ENGINE_TOKEN_SECRET"] = "policy-secret"
        os.environ["LOGIC_ENGINE_ENV"] = "nonprod"
        os.environ["LOGIC_ENGINE_SECRET_PROVIDER"] = "env"
        os.environ["LOGIC_ENGINE_ALLOW_NONPROD_SECRET_FALLBACK"] = "false"

        self.client = TestClient(create_app())
        self.headers_a = {"Authorization": f"Bearer {KEY_A}"}
        self.headers_b = {"Authorization": f"Bearer {KEY_B}"}

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _run_payload(self, principal: str) -> dict:
        return {
            "tenant_id": INTERNAL_TENANT,
            "principal_id": principal,
            "idempotency_key": f"key-{principal}",
            "capability_id": "lead-engineer",
            "input_payload": {},
            "mode": "MANAGED",
            "origin": "INTERNAL",
            "billing_track": "track_1",
            "venture_id": "venture-alpha",
        }

    def test_auth_required(self) -> None:
        response = self.client.get("/v1/catalog/skills")
        self.assertEqual(response.status_code, 401)

    def test_principal_override_is_rejected(self) -> None:
        response = self.client.post("/v1/runs", json=self._run_payload(PRINCIPAL_B), headers=self.headers_a)
        self.assertEqual(response.status_code, 403)

    def test_cross_principal_read_denied(self) -> None:
        create = self.client.post("/v1/runs", json=self._run_payload(PRINCIPAL_A), headers=self.headers_a)
        self.assertEqual(create.status_code, 200)
        run_id = create.json()["run_id"]

        forbidden = self.client.get(f"/v1/runs/{run_id}", headers=self.headers_b)
        self.assertEqual(forbidden.status_code, 403)

    def test_track_identity_contract_enforced(self) -> None:
        bad_payload = self._run_payload(PRINCIPAL_A)
        bad_payload["billing_track"] = "track_2"
        bad_payload["idempotency_key"] = "track2-bad"
        bad_payload.pop("venture_id", None)
        bad_payload["client_id"] = None

        bad = self.client.post("/v1/runs", json=bad_payload, headers=self.headers_a)
        self.assertEqual(bad.status_code, 422)


class KillSwitchTriggerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.service_root = Path(__file__).resolve().parents[1]
        self.tmpdir = tempfile.TemporaryDirectory(prefix="logic-engine-killswitch-")
        self.data_path = Path(self.tmpdir.name) / "store.json"
        self.catalog_path = Path(self.tmpdir.name) / "catalog.json"

        os.environ["LOGIC_ENGINE_REPO_ROOT"] = str(self.repo_root)
        os.environ["LOGIC_ENGINE_DATA_PATH"] = str(self.data_path)
        os.environ["LOGIC_ENGINE_CATALOG_PATH"] = str(self.catalog_path)
        os.environ["LOGIC_ENGINE_PACKAGES_PATH"] = str(self.service_root / "config" / "packages.json")
        os.environ["LOGIC_ENGINE_API_KEYS_PATH"] = str(self.service_root / "config" / "api_keys.json")
        os.environ["LOGIC_ENGINE_DPR_REGISTRY_PATH"] = str(self.service_root / "config" / "dpr_registry.json")
        os.environ["LOGIC_ENGINE_COMPLEXITY_PATH"] = str(self.service_root / "config" / "complexity_multipliers.json")
        os.environ["LOGIC_ENGINE_PROVIDER_PRICING_PATH"] = str(self.service_root / "config" / "provider_pricing.json")
        os.environ["LOGIC_ENGINE_CAPABILITY_POLICY_PATH"] = str(self.service_root / "config" / "capability_policy.json")
        os.environ["LOGIC_ENGINE_TOKEN_SECRET"] = "killswitch-secret"
        os.environ["LOGIC_ENGINE_ENV"] = "nonprod"
        os.environ["LOGIC_ENGINE_SECRET_PROVIDER"] = "env"
        os.environ["LOGIC_ENGINE_ALLOW_NONPROD_SECRET_FALLBACK"] = "false"

        self.engine = LogicEngine(load_settings())
        self.engine.bootstrap_catalog()
        self.auth = AuthContext(tenant_id=INTERNAL_TENANT, principal_id="linktrend-internal-agent", key_id="test")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_level2_halt_blocks_new_runs(self) -> None:
        self.engine.store.set_kill_switch(
            level=KillSwitchLevel.LEVEL_2,
            scope_type=KillSwitchScopeType.TENANT,
            scope_id=INTERNAL_TENANT,
            reason="manual",
            hard_cancel_inflight=False,
            activated_by="ops",
        )

        with self.assertRaises(Exception):
            self.engine.create_run(
                RunCreateRequest(
                    tenant_id=INTERNAL_TENANT,
                    principal_id="linktrend-internal-agent",
                    idempotency_key="halted-run",
                    capability_id="lead-engineer",
                    input_payload={},
                    billing_track="track_1",
                    venture_id="venture-alpha",
                ),
                self.auth,
            )

    def test_security_threshold_trigger_promotes_level2(self) -> None:
        for idx in range(3):
            self.engine.store.record_security_event(
                source=f"source-{idx}",
                event_type="critical_security_exception",
                severity="critical",
            )

        triggered = self.engine.store.evaluate_level2_triggers()
        self.assertIn("security_critical_exceptions_10m", triggered)
        self.assertEqual(self.engine.store.get_kill_switch().level.value, "level_2")


if __name__ == "__main__":
    unittest.main()
