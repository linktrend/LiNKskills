"""Focused qualification and immutable-publication tests for LSALES-WP-005."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "sales-customer-management"
FRAGMENT = ROOT / "catalog/fragments/programs/linksales-sales-customer-management.json"
MANIFEST = ROOT / "evidence/linksales/sales-customer-management/release-manifest.json"
for package in ("contracts", "core", "gateway"):
    sys.path.insert(0, str(ROOT / "packages" / package))

from linkskills_gateway.auth import ActorClaims  # noqa: E402
from linkskills_gateway.persistence import InMemoryGatewayStore  # noqa: E402
from linkskills_gateway.service import ServiceError, SkillsGatewayService  # noqa: E402
from linkskills_core.hashing import directory_manifest_digest  # noqa: E402


def load_json(path: Path):
    """Load a repository JSON fixture."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_helper():
    """Load the offline helper without installing the skill."""
    spec = importlib.util.spec_from_file_location("sales_methodology_helper", SKILL / "scripts/helper_tool.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SalesMethodologyReleaseTests(unittest.TestCase):
    """Verify the settled ownership boundary and publication contract."""

    def test_release_content_identity_is_exact_and_reproducible(self):
        manifest = load_json(MANIFEST)
        for expected in manifest["files"]:
            path = SKILL / expected["path"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(expected["sha256"], actual, expected["path"])
        digest, _ = directory_manifest_digest(SKILL, files=[SKILL / item["path"] for item in manifest["files"]])
        self.assertEqual(manifest["content_digest"], f"skill-release:{digest}")
        self.assertEqual(load_json(FRAGMENT)["release"]["content_digest"], manifest["content_digest"])

    def test_gateway_rejects_unavailable_release_and_mutable_selectors(self):
        fragment = load_json(FRAGMENT)
        release = fragment["release"]
        self.assertEqual("hold", release["availability"])
        self.assertEqual("eval_pending", release["qualification"])
        catalog = {"skills": [{
            "skill_id": fragment["skill_id"],
            "version": release["version"],
            "path": "skills/sales-customer-management",
            "certification_state": "eval_pending",
            "release_hash": release["content_digest"],
        }]}
        actor = ActorClaims(
            actor_id="linksales-fixture",
            actor_kind="agent",
            org_id="synthetic-org",
            scopes=frozenset({"lskills"}),
            permitted_operations=frozenset({"read", "execute"}),
        )
        gateway = SkillsGatewayService(repo_root=ROOT, catalog_index=catalog, store=InMemoryGatewayStore())
        exact = fragment["consumer_contract"]["selector"]
        for version, digest in ((exact["version"], exact["content_digest"]), ("latest", exact["content_digest"]), ("draft", exact["content_digest"]), ("1.1.0", "skill-release:" + "0" * 64)):
            with self.assertRaises(ServiceError):
                gateway.dispatch(
                    "skills_run_start",
                    {"skill_id": fragment["skill_id"], "version": version, "release_hash": digest},
                    actor=actor,
                    idempotency_key=f"fixture-reject-{version}-{digest[-4:]}",
                )
        self.assertFalse(fragment["consumer_contract"]["accepted"])
        self.assertFalse(fragment["consumer_contract"]["execution_authority"])

    def test_settled_boundary_has_no_stale_owner(self):
        stale_owner = "LiNK" + "reach"
        release_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SKILL.rglob("*")
            if path.is_file() and path.suffix in {".md", ".json", ".yaml", ".py"}
        )
        self.assertNotIn(stale_owner, release_text)
        self.assertIn("LiNKsales owns pre-conversion", release_text)
        self.assertIn("LiNKclient owns", release_text)

    def test_qualification_priority_and_handoff_are_independent(self):
        helper = load_helper()
        base = {
            "workflow": "qualification",
            "privacy_classification": "synthetic",
            "source_evidence": [{"ref": "fixture:lead-demo-007", "status": "confirmed"}],
        }
        unranked = helper.normalize_request(base)
        self.assertEqual("qualified", unranked["qualification"]["status"])
        self.assertEqual("unranked", unranked["priority"]["level"])
        ranked = helper.normalize_request({**base, "priority_signals": {"urgency": 2, "impact": 2, "readiness": 1}})
        self.assertEqual("qualified", ranked["qualification"]["status"])
        self.assertEqual("high", ranked["priority"]["level"])
        handoff = helper.normalize_request({**base, "workflow": "onboarding"})
        self.assertTrue(handoff["handoff"]["required"])
        self.assertEqual("LiNKclient", handoff["handoff"]["recipient"])
        self.assertFalse(handoff["handoff"]["accepted"])

    def test_no_send_odoo_payment_or_authority(self):
        helper = load_helper()
        result = helper.normalize_request({
            "workflow": "renewal_risk",
            "privacy_classification": "synthetic",
            "conversion_ref": "conversion-demo-005",
            "source_evidence": [{"ref": "fixture:conversion-demo-005", "status": "confirmed"}],
        })
        self.assertEqual({"sent": False, "applied": False, "mutated_records": False}, result["effects"])
        self.assertEqual("PENDING_APPROVAL", result["status"])
        pack = load_json(SKILL / "references/skill-pack.json")
        forbidden = " ".join(pack["execution"]["forbidden_actions"]).lower()
        for boundary in ("odoo", "send", "pricing", "contracts"):
            self.assertIn(boundary, forbidden)
        self.assertIn("payment", (SKILL / "SKILL.md").read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
