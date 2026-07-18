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


INTERNAL_TENANT = "00000000-0000-0000-0000-000000000001"
PRIMARY_KEY = "test-primary-api-key"
PRIMARY_PRINCIPAL = "linktrend-internal-agent"


class ApiFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.service_root = Path(__file__).resolve().parents[1]
        self.tmpdir = tempfile.TemporaryDirectory(prefix="logic-engine-test-")
        self.data_path = Path(self.tmpdir.name) / "store.json"
        self.catalog_path = Path(self.tmpdir.name) / "catalog.json"
        self.api_keys_path = Path(self.tmpdir.name) / "api_keys.json"
        self.dpr_registry_path = Path(self.tmpdir.name) / "dpr_registry.json"

        self.api_keys_path.write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "key_id": "primary",
                            "api_key": PRIMARY_KEY,
                            "tenant_id": INTERNAL_TENANT,
                            "principal_id": PRIMARY_PRINCIPAL,
                            "state": "active",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.dpr_registry_path.write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "dpr_id": "DPRV3-ALPHA0001",
                            "active": True,
                            "tenant_id": INTERNAL_TENANT,
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
        os.environ["LOGIC_ENGINE_DPR_REGISTRY_PATH"] = str(self.dpr_registry_path)
        os.environ["LOGIC_ENGINE_COMPLEXITY_PATH"] = str(self.service_root / "config" / "complexity_multipliers.json")
        os.environ["LOGIC_ENGINE_PROVIDER_PRICING_PATH"] = str(self.service_root / "config" / "provider_pricing.json")
        os.environ["LOGIC_ENGINE_CAPABILITY_POLICY_PATH"] = str(self.service_root / "config" / "capability_policy.json")
        os.environ["LOGIC_ENGINE_TOKEN_SECRET"] = "test-secret"
        os.environ["LOGIC_ENGINE_ENV"] = "nonprod"
        os.environ["LOGIC_ENGINE_SECRET_PROVIDER"] = "env"
        os.environ["LOGIC_ENGINE_ALLOW_NONPROD_SECRET_FALLBACK"] = "false"

        self.client = TestClient(create_app())
        self.headers = {"Authorization": f"Bearer {PRIMARY_KEY}"}

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_managed_run_and_receipt_flow(self) -> None:
        skills = self.client.get("/v1/catalog/skills", headers=self.headers)
        self.assertEqual(skills.status_code, 200)
        self.assertGreater(len(skills.json()), 0)

        run_payload = {
            "tenant_id": INTERNAL_TENANT,
            "principal_id": PRIMARY_PRINCIPAL,
            "idempotency_key": "run-create-1",
            "capability_id": "lead-engineer",
            "input_payload": {
                "goal": "ship",
                "token_usage": {
                    "model": "gpt-5.4",
                    "prompt_tokens": 1200,
                    "completion_tokens": 400,
                },
            },
            "context_refs": ["ctx://brief/123"],
            "mode": "MANAGED",
            "origin": "INTERNAL",
            "billing_track": "track_1",
            "venture_id": "venture-alpha",
        }

        run_resp = self.client.post("/v1/runs", json=run_payload, headers=self.headers)
        self.assertEqual(run_resp.status_code, 200)
        run_id = run_resp.json()["run_id"]

        issue_resp = self.client.post(
            "/v1/disclosures/issue",
            json={"run_id": run_id, "step_scope": "phase.execute", "idempotency_key": "disclosure-1"},
            headers=self.headers,
        )
        self.assertEqual(issue_resp.status_code, 200)
        self.assertTrue(issue_resp.json()["terminal"])
        receipt_id = issue_resp.json()["receipt_id"]

        run_get = self.client.get(f"/v1/runs/{run_id}", headers=self.headers)
        self.assertEqual(run_get.status_code, 200)
        self.assertEqual(run_get.json()["status"], "completed")

        receipt_get = self.client.get(f"/v1/receipts/{receipt_id}", headers=self.headers)
        self.assertEqual(receipt_get.status_code, 200)
        body = receipt_get.json()
        self.assertEqual(body["run_id"], run_id)
        self.assertEqual(body["retention_class"], "success_metadata_only")
        self.assertGreater(body["cost_breakdown"]["total_cost"], 0)

    def test_idempotency_replay_and_conflict(self) -> None:
        payload = {
            "tenant_id": INTERNAL_TENANT,
            "principal_id": PRIMARY_PRINCIPAL,
            "idempotency_key": "same-key",
            "capability_id": "lead-engineer",
            "input_payload": {"goal": "one"},
            "context_refs": [],
            "mode": "MANAGED",
            "origin": "INTERNAL",
            "billing_track": "track_1",
            "venture_id": "venture-alpha",
        }

        first = self.client.post("/v1/runs", json=payload, headers=self.headers)
        self.assertEqual(first.status_code, 200)

        replay = self.client.post("/v1/runs", json=payload, headers=self.headers)
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.json()["idempotent_replay"])
        self.assertEqual(replay.json()["run_id"], first.json()["run_id"])

        payload["input_payload"] = {"goal": "changed"}
        conflict = self.client.post("/v1/runs", json=payload, headers=self.headers)
        self.assertEqual(conflict.status_code, 409)

    def test_long_running_disclosure_converges_via_polling(self) -> None:
        run_resp = self.client.post(
            "/v1/runs",
            json={
                "tenant_id": INTERNAL_TENANT,
                "principal_id": PRIMARY_PRINCIPAL,
                "idempotency_key": "run-long-1",
                "capability_id": "lead-engineer",
                "input_payload": {
                    "simulate_duration_seconds": 120,
                    "pending_polls": 1,
                    "token_usage": {"model": "gpt-5.4", "prompt_tokens": 100, "completion_tokens": 100},
                },
                "mode": "MANAGED",
                "origin": "INTERNAL",
                "billing_track": "track_1",
                "venture_id": "venture-alpha",
            },
            headers=self.headers,
        )
        self.assertEqual(run_resp.status_code, 200)
        run_id = run_resp.json()["run_id"]

        issue = self.client.post(
            "/v1/disclosures/issue",
            json={"run_id": run_id, "step_scope": "phase.execute", "idempotency_key": "disclosure-long-1"},
            headers=self.headers,
        )
        self.assertEqual(issue.status_code, 200)
        self.assertFalse(issue.json()["terminal"])

        first_poll = self.client.get(f"/v1/runs/{run_id}", headers=self.headers)
        self.assertEqual(first_poll.status_code, 200)
        self.assertEqual(first_poll.json()["status"], "in_progress")

        second_poll = self.client.get(f"/v1/runs/{run_id}", headers=self.headers)
        self.assertEqual(second_poll.status_code, 200)
        self.assertEqual(second_poll.json()["status"], "completed")

    def test_aios_requires_valid_dpr(self) -> None:
        invalid_format = self.client.post(
            "/v1/runs",
            json={
                "tenant_id": INTERNAL_TENANT,
                "principal_id": PRIMARY_PRINCIPAL,
                "idempotency_key": "run-aios-invalid",
                "capability_id": "lead-engineer",
                "input_payload": {},
                "mode": "MANAGED",
                "origin": "AIOS",
                "mission_id": "m-1",
                "task_id": "t-1",
                "dpr_id": "BAD-DPR",
                "billing_track": "track_1",
                "venture_id": "venture-alpha",
            },
            headers=self.headers,
        )
        self.assertEqual(invalid_format.status_code, 400)

        inactive = self.client.post(
            "/v1/runs",
            json={
                "tenant_id": INTERNAL_TENANT,
                "principal_id": PRIMARY_PRINCIPAL,
                "idempotency_key": "run-aios-inactive",
                "capability_id": "lead-engineer",
                "input_payload": {},
                "mode": "MANAGED",
                "origin": "AIOS",
                "mission_id": "m-1",
                "task_id": "t-1",
                "dpr_id": "DPRV3-UNKNOWN01",
                "billing_track": "track_1",
                "venture_id": "venture-alpha",
            },
            headers=self.headers,
        )
        self.assertEqual(inactive.status_code, 400)


if __name__ == "__main__":
    unittest.main()
