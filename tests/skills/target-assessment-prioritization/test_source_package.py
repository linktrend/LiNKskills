from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL_ID = "target-assessment-prioritization"
SKILL = ROOT / "skills" / SKILL_ID
EVIDENCE = ROOT / "evidence" / "certification" / SKILL_ID / "source-package-evidence.json"


class SourcePackageTests(unittest.TestCase):
    def test_progressive_disclosure_and_global_ineligibility_are_explicit(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("Progressive disclosure", "globally ineligible and non-selectable", "not published", "uncertified", "Program authority", "live Platform", "mutate LiNKtarget"):
            self.assertIn(marker, text)
        pack = json.loads((SKILL / "references" / "skill-pack.json").read_text(encoding="utf-8"))
        self.assertFalse(pack["selectable"])
        self.assertEqual(pack["lifecycle_state"], "draft")
        self.assertEqual(pack["certification_state"], "uncertified")
        self.assertEqual([row["disclosure_level"] for row in pack["fragments"]], [1, 2, 3, 4])
        self.assertTrue(all(not values for values in pack["effects"].values()))

    def test_schema_is_closed_and_effects_cannot_encode_selection_or_mutation(self):
        schema = json.loads((SKILL / "references" / "schemas.json").read_text(encoding="utf-8"))
        definitions = schema["definitions"]
        self.assertFalse(definitions["input"]["additionalProperties"])
        self.assertFalse(definitions["output"]["additionalProperties"])
        self.assertEqual(definitions["output"]["properties"]["selectable"]["const"], False)
        effect_properties = definitions["effects"]["properties"]
        self.assertEqual(set(effect_properties), {"messages_sent", "external_calls", "selections", "mutations"})
        self.assertTrue(all(rule["maxItems"] == 0 for rule in effect_properties.values()))
        blocked = set(definitions["input"]["properties"]["requested_action"]["enum"])
        self.assertTrue({"publish", "certify", "mutate_linktarget", "claim_program_authority", "claim_live_platform_use", "infer_sensitive_traits"} <= blocked)

    def test_golden_and_adversarial_evals_are_complete_and_deterministic(self):
        raw = (SKILL / "references" / "eval-suite.json").read_bytes()
        suite = json.loads(raw)
        self.assertEqual(suite["skill_id"], SKILL_ID)
        self.assertEqual(suite["pass_threshold"], 1.0)
        self.assertEqual(len(suite["cases"]), 6)
        self.assertEqual({case["case_type"] for case in suite["cases"]}, {"golden", "adversarial"})
        ids = [case["case_id"] for case in suite["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        hard_failures = set(suite["hard_failure_conditions"])
        self.assertTrue({"linktarget_mutated", "publication_or_certification_claimed", "program_authority_or_live_platform_claimed"} <= hard_failures)
        self.assertEqual(raw, (json.dumps(suite, indent=2) + "\n").encode())

    def test_catalog_fragment_and_index_remain_draft_and_non_certifying(self):
        fragment = json.loads((SKILL / "references" / "catalog-fragment.json").read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / "catalog" / "index.json").read_text(encoding="utf-8"))
        entry = next(row for row in catalog["skills"] if row["skill_id"] == SKILL_ID)
        for key in ("skill_id", "version", "path", "eval_suite_ref", "certification_state"):
            self.assertEqual(entry[key], fragment[key])
        self.assertEqual(entry["certification_state"], "draft")
        self.assertFalse(fragment["selectable"])
        self.assertEqual(fragment["availability"], "source_only")

    def test_source_evidence_hashes_match_and_disclaim_certification(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["certification_status"], "uncertified")
        self.assertEqual(evidence["publication_status"], "not_published")
        self.assertFalse(evidence["program_authority"])
        self.assertFalse(evidence["live_platform_use"])
        self.assertFalse(evidence["selectable"])
        self.assertFalse(evidence["linktarget_mutated"])
        actual = {path.relative_to(SKILL).as_posix(): "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(SKILL.rglob("*")) if path.is_file()}
        self.assertEqual(actual, evidence["artifact_hashes"])


if __name__ == "__main__":
    unittest.main()
