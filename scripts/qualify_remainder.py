#!/usr/bin/env python3
"""Source-only remainder qualification. Never authorizes usable or live publish."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for rel in (
    "packages/eval_runner",
    "packages/core",
    "packages/contracts",
    ".",
):
    sys.path.insert(0, str(REPO / rel))

from linkskills_eval_runner.remainder import qualify_remainder_release_profiles


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_source_drivers(root: Path) -> dict:
    results = []
    failed = 0
    for skill_dir in sorted((root / "skills").glob("*")):
        cases_path = skill_dir / "references" / "remainder-eval-cases.json"
        driver = skill_dir / "scripts" / "eval_driver.py"
        if not cases_path.is_file() or not driver.is_file():
            continue
        payload = json.loads(cases_path.read_text(encoding="utf-8"))
        cases = payload.get("cases") or {}
        for case_id in sorted(cases):
            proc = subprocess.run(
                [sys.executable, str(driver), "--case", case_id],
                capture_output=True,
                text=True,
                cwd=str(skill_dir),
            )
            ok = proc.returncode == 0 and '"status": "error"' not in proc.stdout
            if not ok:
                failed += 1
            results.append(
                {
                    "skillId": skill_dir.name,
                    "caseId": case_id,
                    "exitCode": proc.returncode,
                    "ok": ok,
                }
            )
    return {
        "evidenceClass": "source_executable_not_production",
        "driverRuns": len(results),
        "failed": failed,
        "ok": failed == 0,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    matrix = qualify_remainder_release_profiles(REPO)
    drivers = run_source_drivers(REPO)
    report = {
        "generatedAt": _utc(),
        "issue": 374,
        "usableClaimed": False,
        "authorizesUsable": False,
        "matrix": {
            "ok": matrix["ok"],
            "remainderCount": matrix["remainderCount"],
            "missingExecutable": matrix["missingExecutable"],
            "missingFamilies": matrix["missingFamilies"],
            "evalPending": len(matrix["evalPending"]),
            "liveQualificationBoundary": matrix["liveQualificationBoundary"],
            "initialProductionSuccessor": matrix["initialProductionSuccessor"],
        },
        "sourceDrivers": {
            "ok": drivers["ok"],
            "driverRuns": drivers["driverRuns"],
            "failed": drivers["failed"],
            "evidenceClass": drivers["evidenceClass"],
        },
        "hostedSealedEvaluator": {
            "executed": False,
            "reason": "cloud_worker_lacks_nonprivileged_digest_pinned_evaluator_and_issuer_injection",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.write:
        out = REPO / "evidence" / "issue-374" / "remainder-source-qualification.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        slim = dict(report)
        slim["sourceDrivers"] = {
            k: drivers[k] for k in ("ok", "driverRuns", "failed", "evidenceClass")
        }
        out.write_text(json.dumps(slim, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        plan = REPO / "configs" / "qualification" / "remainder-54-plan.json"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text(
            json.dumps(
                {
                    "schemaVersion": "1.0",
                    "kind": "remainder-54-qualification-release-plan",
                    "disabledByDefault": True,
                    "usableClaimed": False,
                    "authorizesUsable": False,
                    "skillRetrievalCreatesCapabilityGrants": False,
                    "initialProductionSuccessor": matrix["initialProductionSuccessor"],
                    "remainderCount": 54,
                    "targetImmutableProductionReleasesAfterServer01": 59,
                    "runtimeProfile": "cursor-macos",
                    "combinations": [
                        {
                            "id": row["id"],
                            "skillId": row["skillId"],
                            "version": row["version"],
                            "lifecycle": row["lifecycle"],
                            "executableCases": row["executableCases"],
                            "missingFamilies": row["missingFamilies"],
                            "evidenceClass": row["evidenceClass"],
                            "reason": row["reason"],
                        }
                        for row in matrix["combinations"]
                    ],
                    "server01": {
                        "qualify": "qualify --package /tmp/linkskills-hosted-sealed/package.json",
                        "publish": (
                            "python3 /opt/linkskills/scripts/provider_release.py publish "
                            "--package <path> --expected-commit <accepted image source commit>"
                        ),
                        "never": [
                            "workstation privileged docker certify script",
                            "global consumer activation",
                            "capability grants from skill retrieval",
                        ],
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    return 0 if matrix["ok"] and drivers["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
