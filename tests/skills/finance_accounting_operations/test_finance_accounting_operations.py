"""Focused PKT-15 contract and boundary regressions."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "packages" / "contracts"))

from linkskills_contracts import validate_instance  # noqa: E402


FINANCE = REPO_ROOT / "skills" / "finance-accounting-operations"
CONTROLLER = REPO_ROOT / "skills" / "studio-controller"


DIGEST = "sha256:" + ("a" * 64)
COMMIT = "8964a1012dc9ca9e4cb2a43c370f23aab55aeefd"
TREE = "111bc43370683a72e94c775f2a968bc1c7f8a9f3"
ROLLBACK_COMMIT = "2d24e55e96caf4fc2ec37330d30d740805904368"
ROLLBACK_TREE = "fa328aa50c7febaefb22f9c22f883587c49e9e3f"
RELEASE_METADATA = {
    "release_tag": "v1.0.0",
    "skill_id": "finance-accounting-operations",
    "source_commit": COMMIT,
    "source_tree": TREE,
}
RELEASE_DIGEST = "sha256:" + hashlib.sha256(
    json.dumps(RELEASE_METADATA, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
OFFICIAL_SOURCES = [
    "https://platform.claude.com/docs/en/about-claude/models/overview",
    "https://www.anthropic.com/legal/commercial-terms",
    "https://www.odoo.com/documentation/19.0/developer/reference/external_api.html",
    "https://www.odoo.com/documentation/19.0/legal/licenses.html",
]


def valid_input() -> dict:
    return {
        "period": "2026-07",
        "currency": "USD",
        "odoo_contract": {
            "contract_id": "odoo-read-v1",
            "contract_version": "19.0-readonly",
            "read_operations": [
                "invoices.read",
                "payments.read",
                "expenses.read",
                "budgets.read",
                "cash_flow.read",
                "period_status.read",
            ],
            "authority_owner": "consumer-adapter",
            "escalation_contact": "principal",
        },
        "snapshot": {
            "content_digest": DIGEST,
            "retrieved_at": "2026-08-24T00:00:00Z",
            "period": "2026-07",
            "currency": "USD",
            "source_owner": "synthetic-fixture",
            "records": [],
            "source_references": OFFICIAL_SOURCES,
        },
        "requested_views": ["cash_flow_forecast", "budget_actual"],
        "data_classification": "synthetic",
        "task_id": "finance-pkt15-20260824",
    }


def valid_output() -> dict:
    return {
        "status": "COMPLETED",
        "brief": {"observations": []},
        "provenance": {
            "release_tag": "v1.0.0",
            "source_commit": COMMIT,
            "source_tree": TREE,
            "content_digest": RELEASE_DIGEST,
            "input_snapshot_digest": DIGEST,
            "contract_id": "odoo-read-v1",
            "contract_version": "19.0-readonly",
            "source_references": OFFICIAL_SOURCES,
        },
        "effects": {"external_calls": [], "mutations": []},
        "approval": {"status": "NOT_REQUIRED"},
        "contract_status": "VERIFIED_READ_ONLY",
        "rollback_release": "catalog:starter-foundation@1.0.0",
        "rollback_parent_commit": ROLLBACK_COMMIT,
        "rollback_parent_tree": ROLLBACK_TREE,
    }


class FinanceOperationsPackageTests(unittest.TestCase):
    def test_manifest_shape_and_contracts(self) -> None:
        required = (
            "SKILL.md",
            "advanced/advanced.md",
            "examples/success-pattern.md",
            "examples/error-recovery.md",
            "references/api-specs.md",
            "references/changelog.md",
            "references/eval-suite.yaml",
            "references/execution-profile.json",
            "references/skill-pack.json",
            "references/old-patterns.md",
            "references/schemas.json",
            "scripts/README.md",
            "scripts/helper_tool.py",
        )
        for rel in required:
            self.assertTrue((FINANCE / rel).is_file(), rel)
        schema = json.loads((FINANCE / "references/schemas.json").read_text(encoding="utf-8"))
        self.assertEqual(
            set(schema["definitions"]["input"]["required"]),
            {"period", "currency", "odoo_contract", "snapshot", "requested_views", "data_classification"},
        )
        self.assertIn("effects", schema["definitions"]["output"]["required"])
        self.assertIn("rollback_release", schema["definitions"]["output"]["required"])
        self.assertEqual(schema["definitions"]["output"]["properties"]["provenance"]["properties"]["content_digest"]["const"], RELEASE_DIGEST)

    def test_eval_suite_covers_required_classes_and_views(self) -> None:
        text = (FINANCE / "references/eval-suite.yaml").read_text(encoding="utf-8")
        for case_class in ("ordinary", "ambiguous", "adversarial", "authority", "tool_failure", "privacy"):
            self.assertIn(f"class: {case_class}", text)
        for view in ("cash", "budget", "invoice", "payment", "expense", "close", "runway"):
            self.assertIn(view, text.lower())

    def test_read_only_and_fail_closed_boundary(self) -> None:
        skill = (FINANCE / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("never invoke odoo", skill)
        self.assertIn("never create or mutate", skill)
        self.assertIn("pending_approval", skill)
        self.assertNotIn("lsl_finance", skill)
        specs = (FINANCE / "references/api-specs.md").read_text(encoding="utf-8").lower()
        for operation in ("invoice.create", "payment.post", "journal.post", "period.close", "credential.read"):
            self.assertIn(operation, specs)
        for source_marker in (
            "anthropic claude platform",
            "commercial terms of service",
            "odoo 19",
            "lgpl-3",
            "odoo enterprise edition license v1.0",
            "odoo proprietary license v1.0",
        ):
            self.assertIn(source_marker, specs)

    def test_contract_schemas_reject_incomplete_and_unsafe_records(self) -> None:
        schemas = json.loads((FINANCE / "references/schemas.json").read_text(encoding="utf-8"))["definitions"]

        incomplete_input = deepcopy(valid_input())
        incomplete_input["odoo_contract"] = {}
        self.assertFalse(validate_instance(incomplete_input, schemas["input"]).ok)

        unknown_operation = deepcopy(valid_input())
        unknown_operation["odoo_contract"]["read_operations"] = ["invoice.create"]
        self.assertFalse(validate_instance(unknown_operation, schemas["input"]).ok)

        incomplete_snapshot = deepcopy(valid_input())
        del incomplete_snapshot["snapshot"]["content_digest"]
        self.assertFalse(validate_instance(incomplete_snapshot, schemas["input"]).ok)

        snapshot_pii = deepcopy(valid_input())
        snapshot_pii["snapshot"]["customer_email"] = "customer@example.com"
        self.assertFalse(validate_instance(snapshot_pii, schemas["input"]).ok)

        record_pii = deepcopy(valid_input())
        record_pii["snapshot"]["records"] = [{"kind": "invoice", "amount": "12.50", "customer_email": "customer@example.com"}]
        self.assertFalse(validate_instance(record_pii, schemas["input"]).ok)

        unapproved_snapshot_source = deepcopy(valid_input())
        unapproved_snapshot_source["snapshot"]["source_references"] = ["https://example.invalid/finance"]
        self.assertFalse(validate_instance(unapproved_snapshot_source, schemas["input"]).ok)

        unsafe_output = deepcopy(valid_output())
        unsafe_output["effects"]["mutations"] = ["invoice.create"]
        self.assertFalse(validate_instance(unsafe_output, schemas["output"]).ok)

        incomplete_output = deepcopy(valid_output())
        del incomplete_output["provenance"]["source_commit"]
        self.assertFalse(validate_instance(incomplete_output, schemas["output"]).ok)

        wrong_rollback = deepcopy(valid_output())
        wrong_rollback["rollback_release"] = "catalog:unqualified@9.9.9"
        self.assertFalse(validate_instance(wrong_rollback, schemas["output"]).ok)

        wrong_rollback_tree = deepcopy(valid_output())
        wrong_rollback_tree["rollback_parent_tree"] = "0" * 40
        self.assertFalse(validate_instance(wrong_rollback_tree, schemas["output"]).ok)

        unapproved_source = deepcopy(valid_output())
        unapproved_source["provenance"]["source_references"] = ["https://example.invalid/finance"]
        self.assertFalse(validate_instance(unapproved_source, schemas["output"]).ok)

        unrelated_release_digest = deepcopy(valid_output())
        unrelated_release_digest["provenance"]["content_digest"] = DIGEST
        self.assertFalse(validate_instance(unrelated_release_digest, schemas["output"]).ok)

    def test_contract_schemas_accept_evidence_complete_read_only_records(self) -> None:
        schemas = json.loads((FINANCE / "references/schemas.json").read_text(encoding="utf-8"))["definitions"]
        self.assertTrue(validate_instance(valid_input(), schemas["input"]).ok)
        self.assertTrue(validate_instance(valid_output(), schemas["output"]).ok)

    def test_offline_helpers_have_no_external_effects(self) -> None:
        finance_helper = FINANCE / "scripts" / "helper_tool.py"
        controller_helper = CONTROLLER / "scripts" / "helper_tool.py"
        payload = json.dumps({"records": [{"kind": "invoice", "amount": "12.50"}]})
        result = subprocess.run(
            [sys.executable, str(finance_helper)], input=payload, text=True, capture_output=True, check=True
        )
        finance_output = json.loads(result.stdout)
        self.assertEqual(finance_output["totals"]["invoice"], "12.50")
        self.assertEqual(finance_output["external_calls"], [])
        self.assertEqual(finance_output["mutations"], [])

        controller_payload = json.dumps({"observations": [{"status": "CONFLICTING"}]})
        result = subprocess.run(
            [sys.executable, str(controller_helper)],
            input=controller_payload,
            text=True,
            capture_output=True,
            check=True,
        )
        controller_output = json.loads(result.stdout)
        self.assertEqual(controller_output["status_counts"]["CONFLICTING"], 1)
        self.assertEqual(controller_output["external_calls"], [])
        self.assertEqual(controller_output["mutations"], [])


class StudioControllerMigrationTests(unittest.TestCase):
    def test_controller_no_longer_requires_ledger_or_connector(self) -> None:
        skill = (CONTROLLER / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("review primitive", skill)
        self.assertIn("system of record", skill)
        self.assertIn("studio-controller@v1.0.0", (CONTROLLER / "references/api-specs.md").read_text(encoding="utf-8"))
        self.assertNotIn("lsl_finance", skill)


if __name__ == "__main__":
    unittest.main()
