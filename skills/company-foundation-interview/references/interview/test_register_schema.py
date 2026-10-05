"""Offline contract tests for the portable interview register schema."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from urllib.parse import urldefrag, urljoin

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE.parent / "schemas.json"
TEMPLATE_PATH = HERE / "fact-register-template.json"
FIXTURE_PATH = HERE / "register-schema-cases.json"


class InterviewRegisterSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema_document = json.loads(SCHEMA_PATH.read_text())
        cls.template = json.loads(TEMPLATE_PATH.read_text())
        cls.fixtures = json.loads(FIXTURE_PATH.read_text())
        Draft202012Validator.check_schema(cls.schema_document)
        cls.schema_uri = SCHEMA_PATH.as_uri()
        registry = Registry().with_resource(
            cls.schema_uri, Resource.from_contents(cls.schema_document)
        )
        cls.register_schema = {
            "$schema": cls.schema_document["$schema"],
            "$ref": f"{cls.schema_uri}#/definitions/interview_register",
        }
        cls.validator = Draft202012Validator(
            cls.register_schema, registry=registry, format_checker=FormatChecker()
        )

    def errors(self, instance: object) -> list:
        return sorted(self.validator.iter_errors(instance), key=lambda error: list(error.absolute_path))

    @staticmethod
    def mutate(instance: dict, mutation: dict) -> dict:
        result = copy.deepcopy(instance)
        parts = [part.replace("~1", "/").replace("~0", "~") for part in mutation["path"].lstrip("/").split("/")]
        target = result
        for part in parts[:-1]:
            target = target[int(part)] if isinstance(target, list) else target[part]
        key = parts[-1]
        if mutation["op"] == "remove":
            if isinstance(target, list):
                del target[int(key)]
            else:
                del target[key]
        elif mutation["op"] == "replace":
            if isinstance(target, list):
                target[int(key)] = mutation["value"]
            else:
                target[key] = mutation["value"]
        else:
            raise AssertionError(f"unsupported fixture operation: {mutation['op']}")
        return result

    def test_neutral_template_is_valid_and_contains_no_implied_facts(self) -> None:
        contract_ref = self.fixtures["schema_ref"]
        target_uri, target_fragment = urldefrag(urljoin(TEMPLATE_PATH.as_uri(), contract_ref))
        self.assertEqual(target_uri, self.schema_uri)
        self.assertEqual(target_fragment, "/definitions/interview_register")
        self.assertEqual(self.errors(self.template), [])
        self.assertEqual(self.template["facts"], [])
        self.assertEqual(self.template["unresolved_decisions"], [])
        self.assertIsNone(self.template["native_checkpoint_ref"])

    @staticmethod
    def semantic_errors(register: dict) -> list[str]:
        fact_ids = [fact["fact_id"] for fact in register["facts"]]
        known_fact_ids = set(fact_ids)
        issues = []
        if len(known_fact_ids) != len(fact_ids):
            issues.append("duplicate fact_id")
        facts_by_id = {fact["fact_id"]: fact for fact in register["facts"]}
        for fact in register["facts"]:
            for other_id in fact["contradicts"]:
                other = facts_by_id.get(other_id)
                if other is None:
                    issues.append(f"dangling contradiction reference: {other_id}")
                elif other_id == fact["fact_id"]:
                    issues.append(f"self contradiction reference: {other_id}")
                elif fact["fact_id"] not in other["contradicts"]:
                    issues.append(f"non-reciprocal contradiction reference: {other_id}")
        question_ids = {answer["question_id"] for answer in register["answered_questions"]}
        if len(question_ids) != len(register["answered_questions"]):
            issues.append("duplicate question_id")
        checkpoint = register["native_checkpoint_ref"]
        if checkpoint is not None:
            if not set(checkpoint["answered_question_ids"]).issubset(question_ids):
                issues.append("checkpoint references an unknown answered question")
            open_ids = known_fact_ids | {item["decision_id"] for item in register["unresolved_decisions"]} | question_ids
            if not set(checkpoint["open_item_ids"]).issubset(open_ids):
                issues.append("checkpoint references an unknown open item")
        return issues

    def test_synthetic_register_with_provenance_conflicts_and_resume_state_is_valid(self) -> None:
        register = self.fixtures["valid_register"]
        self.assertEqual(self.errors(register), [])
        self.assertEqual(self.semantic_errors(register), [])

    def test_dangling_conflict_reference_is_rejected_semantically(self) -> None:
        register = copy.deepcopy(self.fixtures["valid_register"])
        register["facts"][0]["contradicts"] = ["synthetic:missing-fact"]
        self.assertEqual(self.errors(register), [])
        self.assertIn("dangling contradiction reference: synthetic:missing-fact", self.semantic_errors(register))

    def test_negative_cases_fail_at_the_intended_contract_boundary(self) -> None:
        baseline = self.fixtures["valid_register"]
        for case in self.fixtures["negative_cases"]:
            with self.subTest(case_id=case["case_id"]):
                invalid = baseline
                for mutation in case["mutations"]:
                    invalid = self.mutate(invalid, mutation)
                errors = self.errors(invalid)
                self.assertTrue(errors, f"{case['case_id']} unexpectedly passed")
                wanted = tuple(case["expected_error_path"])
                self.assertTrue(
                    any(tuple(error.absolute_path)[: len(wanted)] == wanted for error in errors),
                    f"{case['case_id']} failed at unexpected paths: "
                    f"{[list(error.absolute_path) for error in errors]}",
                )


if __name__ == "__main__":
    unittest.main()
