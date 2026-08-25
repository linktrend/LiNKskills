"""Focused tests for fail-closed PKT-26 reconciliation."""

from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from reconcile_final_dod import reconcile


TEMPLATE = Path(__file__).with_name("pkt-26-final-reconciliation-receipt.template.json")


class FinalDodReconciliationTests(unittest.TestCase):
    @staticmethod
    def _write_receipt(directory: str, name: str, payload: dict[str, object]) -> tuple[Path, str]:
        path = Path(directory) / name
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_preparatory_template_is_hold_without_external_io(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        report = reconcile(payload)
        self.assertEqual(report["decision"], "HOLD")
        self.assertFalse(report["external_io_performed"])
        self.assertTrue(any("not_supplied" in blocker for blocker in report["blockers"]))
        self.assertFalse(report["claims"]["production_proven"])

    def test_complete_requires_every_slot_and_rollback_receipt(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        commit = "a" * 40
        tree = "b" * 40
        with tempfile.TemporaryDirectory() as directory:
            payload["status"] = "FINAL_RECONCILIATION"
            payload["decision"] = "COMPLETE"
            for dependency_name, dependency in payload["dependencies"].items():
                dependency_receipt_path, dependency_digest = self._write_receipt(
                    directory,
                    f"{dependency_name.lower()}.json",
                    {
                        "packet": dependency_name,
                        "evidence_class": "source",
                        "repository": "owner/dependency",
                        "ref": "refs/heads/exact",
                        "commit": commit,
                        "tree": tree,
                    },
                )
                dependency.update(
                    {
                        "admission": "ADMITTED",
                        "receipt_ref": dependency_receipt_path.name,
                        "receipt_digest": dependency_digest,
                    }
                )
            slot_receipts = []
            for slot in payload["receipt_slots"]:
                command_digest = hashlib.sha256(f"command:{slot['slot']}".encode()).hexdigest()
                result_digest = hashlib.sha256(f"result:{slot['slot']}".encode()).hexdigest()
                receipt_payload = {
                    "packet": slot["packet"],
                    "slot": slot["slot"],
                    "evidence_class": slot["evidence_class"],
                    "repository": "owner/repo",
                    "ref": "refs/heads/exact",
                    "commit": commit,
                    "tree": tree,
                    "command_or_profile_digest": command_digest,
                    "result_digest": result_digest,
                }
                if slot["slot"] in {"hosted_stage", "vps", "production"}:
                    receipt_payload["environment"] = slot["environment"]
                receipt, digest = self._write_receipt(directory, f"{slot['slot']}.json", receipt_payload)
                slot_receipts.append(receipt.name)
                slot.update({
                    "supplied": True,
                    "receipt_ref": receipt.name,
                    "receipt_digest": digest,
                    "repository": "owner/repo",
                    "ref": "refs/heads/exact",
                    "commit": commit,
                    "tree": tree,
                    "command_or_profile_digest": command_digest,
                    "result_digest": result_digest,
                    "rollback_ref": "rollback.json",
                    "handoff_ref": "handoff.md",
                })
            for row in payload["ledger"]:
                row["classification"] = "proven"
                row["required_evidence_classes"] = ["source", "consumer", "hosted/stage", "VPS", "E2E", "production"]
                row["receipt_refs"] = slot_receipts
            rollback_identity = {
                "repository": "owner/repo",
                "ref": "refs/heads/exact",
                "commit": commit,
                "tree": tree,
            }
            rollback_action = "restore-prior-release"
            rollback_result = hashlib.sha256(b"rollback-result").hexdigest()
            rollback_receipt, rollback_digest = self._write_receipt(
                directory,
                "rollback.json",
                {
                    "identity": rollback_identity,
                    "action": rollback_action,
                    "result_digest": rollback_result,
                },
            )
            for value in payload["rollback_recovery"].values():
                if isinstance(value, dict):
                    value.update(
                        {
                            "status": "PROVEN",
                            "receipt_ref": rollback_receipt.name,
                            "receipt_digest": rollback_digest,
                            "identity": rollback_identity,
                            "action": rollback_action,
                            "result_digest": rollback_result,
                        }
                    )
            report = reconcile(payload, receipt_root=Path(directory))
        self.assertEqual(report["decision"], "COMPLETE")
        self.assertEqual(report["blockers"], [])

    def test_fabricated_complete_payload_with_unmatched_receipt_facts_is_hold(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload["status"] = "FINAL_RECONCILIATION"
        payload["decision"] = "COMPLETE"
        with tempfile.TemporaryDirectory() as directory:
            receipt, digest = self._write_receipt(directory, "receipt.json", {"receipt": "exact"})
            slot = payload["receipt_slots"][0]
            slot.update(
                {
                    "supplied": True,
                    "receipt_ref": receipt.name,
                    "receipt_digest": digest,
                    "repository": "owner/repo",
                    "ref": "refs/heads/exact",
                    "commit": "a" * 40,
                    "tree": "b" * 40,
                    "command_or_profile_digest": digest,
                    "result_digest": digest,
                    "rollback_ref": "rollback.json",
                    "handoff_ref": "handoff.md",
                }
            )
            report = reconcile(payload, receipt_root=Path(directory))
        self.assertEqual(report["decision"], "HOLD")
        self.assertIn("slot:provider:receipt_packet_mismatch", report["blockers"])
        self.assertIn("rollback:source:not_proven", report["blockers"])

    def test_ledger_receipt_ref_must_bind_to_verified_receipt(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload["ledger"][0].update(
            {"classification": "proven", "required_evidence_classes": ["source"], "receipt_refs": ["missing.json"]}
        )
        report = reconcile(payload)
        self.assertIn("ledger[0]:receipt_digest_unbound:0", report["blockers"])

    def test_required_evidence_class_must_be_supplied_on_referenced_receipt(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload["ledger"][0].update(
            {"classification": "proven", "required_evidence_classes": ["source"], "receipt_refs": []}
        )
        report = reconcile(payload)
        self.assertIn("ledger[0]:evidence_class_missing:source", report["blockers"])

    def test_ledger_requires_nonempty_evidence_classes_and_receipt_refs(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload["ledger"][0].update(
            {"classification": "not_proven", "required_evidence_classes": [], "receipt_refs": []}
        )
        report = reconcile(payload)
        self.assertIn("ledger[0]:required_evidence_classes_missing", report["blockers"])
        self.assertIn("ledger[0]:receipt_refs_missing", report["blockers"])

    def test_slot_receipt_packet_command_and_result_must_match_claim(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            receipt, digest = self._write_receipt(
                directory,
                "slot.json",
                {
                    "packet": "wrong-packet",
                    "command_or_profile_digest": "c" * 64,
                    "result_digest": "d" * 64,
                },
            )
            payload["receipt_slots"][0].update(
                {
                    "supplied": True,
                    "receipt_ref": receipt.name,
                    "receipt_digest": digest,
                    "repository": "owner/repo",
                    "ref": "refs/heads/exact",
                    "commit": "a" * 40,
                    "tree": "b" * 40,
                    "command_or_profile_digest": "e" * 64,
                    "result_digest": "f" * 64,
                    "rollback_ref": "rollback.json",
                    "handoff_ref": "handoff.md",
                }
            )
            report = reconcile(payload, receipt_root=Path(directory))
        self.assertIn("slot:provider:receipt_packet_mismatch", report["blockers"])
        self.assertIn("slot:provider:receipt_command_or_profile_digest_mismatch", report["blockers"])
        self.assertIn("slot:provider:receipt_result_digest_mismatch", report["blockers"])

    def test_rollback_receipt_identity_action_and_result_must_match(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            receipt, digest = self._write_receipt(
                directory,
                "rollback.json",
                {
                    "identity": {"repository": "other/repo", "ref": "refs/heads/other", "commit": "c" * 40, "tree": "d" * 40},
                    "action": "wrong-action",
                    "result_digest": "e" * 64,
                },
            )
            payload["rollback_recovery"]["source"].update(
                {
                    "status": "PROVEN",
                    "receipt_ref": receipt.name,
                    "receipt_digest": digest,
                    "identity": {"repository": "owner/repo", "ref": "refs/heads/exact", "commit": "a" * 40, "tree": "b" * 40},
                    "action": "restore-prior-release",
                    "result_digest": "f" * 64,
                }
            )
            report = reconcile(payload, receipt_root=Path(directory))
        self.assertIn("rollback:source:identity_mismatch", report["blockers"])
        self.assertIn("rollback:source:action_mismatch", report["blockers"])
        self.assertIn("rollback:source:result_digest_mismatch", report["blockers"])

    def test_rollback_identity_requires_exact_git_ids(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload["rollback_recovery"]["source"].update(
            {
                "status": "PROVEN",
                "receipt_ref": "rollback.json",
                "receipt_digest": "a" * 64,
                "identity": {
                    "repository": "owner/repo",
                    "ref": "refs/heads/exact",
                    "commit": "short",
                    "tree": "also-short",
                },
                "action": "restore",
                "result_digest": "b" * 64,
            }
        )
        report = reconcile(payload)
        self.assertIn("rollback:source:identity_commit_invalid", report["blockers"])
        self.assertIn("rollback:source:identity_tree_invalid", report["blockers"])

    def test_dependency_receipt_reference_and_digest_are_verified(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "pkt25-receipt.json"
            receipt.write_text('{"receipt":"exact"}\n', encoding="utf-8")
            digest = hashlib.sha256(receipt.read_bytes()).hexdigest()
            payload["dependencies"]["PKT-25"].update(
                {
                    "admission": "ADMITTED",
                    "receipt_ref": receipt.name,
                    "receipt_digest": digest,
                }
            )
            result = reconcile(payload, receipt_root=Path(directory))
            self.assertIn("PKT-25:receipt_repository_missing", result["dependency_problems"])
            self.assertIn("PKT-25:receipt_packet_mismatch", result["dependency_problems"])

            payload["dependencies"]["PKT-25"]["receipt_digest"] = "0" * 64
            mismatch = reconcile(payload, receipt_root=Path(directory))
            self.assertIn("PKT-25:receipt_digest_mismatch", mismatch["dependency_problems"])

    def test_absolute_receipt_reference_cannot_escape_receipt_root(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            receipt.write_text("{}\n", encoding="utf-8")
            payload["dependencies"]["PKT-25"].update(
                {
                    "admission": "ADMITTED",
                    "receipt_ref": str(receipt),
                    "receipt_digest": hashlib.sha256(receipt.read_bytes()).hexdigest(),
                }
            )
            result = reconcile(payload, receipt_root=Path(directory))
        self.assertIn("PKT-25:receipt_ref_outside_root", result["dependency_problems"])

    def test_opaque_dependency_receipt_cannot_satisfy_exact_binding(self) -> None:
        payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload["dependencies"]["PKT-25"].update(
            {"admission": "ADMITTED", "receipt_ref": "opaque:invented", "receipt_digest": "a" * 64}
        )
        result = reconcile(payload)
        self.assertIn("PKT-25:receipt_ref_unresolvable", result["dependency_problems"])


if __name__ == "__main__":
    unittest.main()
