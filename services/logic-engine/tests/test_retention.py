from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sys

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from logic_engine.config import load_settings  # noqa: E402
from logic_engine.engine import AuthContext, LogicEngine  # noqa: E402
from logic_engine.types import DisclosureIssueRequest, ExecutionMode, RunCreateRequest  # noqa: E402


INTERNAL_TENANT = "00000000-0000-0000-0000-000000000001"
PRINCIPAL = "linktrend-internal-agent"


class RetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.service_root = Path(__file__).resolve().parents[1]
        self.tmpdir = tempfile.TemporaryDirectory(prefix="logic-engine-retention-")
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
        os.environ["LOGIC_ENGINE_TOKEN_SECRET"] = "retention-secret"
        os.environ["LOGIC_ENGINE_ENV"] = "nonprod"
        os.environ["LOGIC_ENGINE_SECRET_PROVIDER"] = "env"
        os.environ["LOGIC_ENGINE_ALLOW_NONPROD_SECRET_FALLBACK"] = "false"

        self.engine = LogicEngine(load_settings())
        self.engine.bootstrap_catalog()
        self.auth = AuthContext(tenant_id=INTERNAL_TENANT, principal_id=PRINCIPAL, key_id="test")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_failure_diagnostics_purged_after_30_days_and_financial_kept_7y(self) -> None:
        run = self.engine.create_run(
            RunCreateRequest(
                tenant_id=INTERNAL_TENANT,
                principal_id=PRINCIPAL,
                idempotency_key="ret-run-1",
                capability_id="lead-engineer",
                input_payload={
                    "force_error": True,
                    "token_usage": {"model": "gpt-5.4", "prompt_tokens": 100, "completion_tokens": 50},
                },
                mode=ExecutionMode.MANAGED,
                billing_track="track_1",
                venture_id="venture-alpha",
            ),
            self.auth,
        )
        disclosure = self.engine.issue_disclosure(
            DisclosureIssueRequest(run_id=run.run_id, step_scope="phase.execute", idempotency_key="ret-disclosure-1"),
            self.auth,
        )
        run_before = self.engine.get_run(run.run_id)
        self.assertEqual(run_before.status.value, "evaluation_failed")
        self.assertIsNotNone(run_before.diagnostics_redacted)

        receipt_before = self.engine.get_receipt(disclosure.receipt_id)
        self.assertEqual(receipt_before.retention_class.value, "failure_redacted_30d")

        after_31 = datetime.now(timezone.utc) + timedelta(days=31)
        self.engine.store.retention_sweep(now=after_31)

        run_after = self.engine.get_run(run.run_id)
        self.assertIsNone(run_after.diagnostics_redacted)

        # Receipt and disclosure metadata should still exist before 180d.
        receipt_still = self.engine.get_receipt(disclosure.receipt_id)
        self.assertEqual(receipt_still.run_id, run.run_id)

        # 7-year ledger retention should keep financial rows at 180d horizon.
        self.assertGreater(len(self.engine.store._state["financial_ledger"]), 0)

    def test_disclosure_receipt_audit_purged_after_180_days(self) -> None:
        run = self.engine.create_run(
            RunCreateRequest(
                tenant_id=INTERNAL_TENANT,
                principal_id=PRINCIPAL,
                idempotency_key="ret-run-2",
                capability_id="lead-engineer",
                input_payload={"token_usage": {"model": "gpt-5.4", "prompt_tokens": 50, "completion_tokens": 50}},
                mode=ExecutionMode.MANAGED,
                billing_track="track_1",
                venture_id="venture-alpha",
            ),
            self.auth,
        )
        disclosure = self.engine.issue_disclosure(
            DisclosureIssueRequest(run_id=run.run_id, step_scope="phase.execute", idempotency_key="ret-disclosure-2"),
            self.auth,
        )

        after_181 = datetime.now(timezone.utc) + timedelta(days=181)
        sweep = self.engine.store.retention_sweep(now=after_181)
        self.assertGreaterEqual(sweep.purged_disclosures, 1)
        self.assertGreaterEqual(sweep.purged_receipts, 1)
        self.assertGreaterEqual(sweep.purged_audit_logs, 1)

        with self.assertRaises(Exception):
            self.engine.get_receipt(disclosure.receipt_id)


if __name__ == "__main__":
    unittest.main()
