#!/usr/bin/env python3
"""Librarian boundary proofs for external update candidates."""

from __future__ import annotations

import unittest

from linkskills_librarian.worker import DomainWorker


class ExternalCandidateReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = DomainWorker()
        self.evidence = {
            "diff": {"changed": 1}, "license": {"compatible": True},
            "security": {"passed": True}, "compatibility": {"passed": True},
            "evaluation": {"passed": True}, "customization": {"none": True},
            "feedback": {"count": 0},
        }

    def test_each_outcome_is_explicit_and_apply_stays_platform_owned(self):
        for index, outcome in enumerate(("accept", "adapt", "postpone", "reject")):
            result = self.worker.review_update_candidate({
                "candidate_id": f"candidate-{index}", "outcome": outcome,
                "reviewer": "librarian", "evidence": self.evidence,
            })
            self.assertEqual(result["outcome"], outcome)
            self.assertFalse(result["direct_activation"])
            self.assertEqual(result["platform_apply_required"], outcome in {"accept", "adapt"})

    def test_missing_evidence_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "missing_review_evidence"):
            self.worker.review_update_candidate({
                "candidate_id": "candidate-1", "outcome": "accept",
                "reviewer": "librarian", "evidence": {"security": {"passed": True}},
            })


if __name__ == "__main__":
    unittest.main()
