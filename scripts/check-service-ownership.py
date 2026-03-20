#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, Set

ALLOWED_OWNERS = {"gws", "ltr"}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    matrix_path = repo_root / "configs" / "service_ownership.json"
    if not matrix_path.exists():
        print(json.dumps({"status": "error", "message": f"Missing matrix file: {matrix_path}"}))
        return 1

    try:
        payload = json.loads(matrix_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {exc}"}))
        return 1

    services = payload.get("services")
    if not isinstance(services, list) or not services:
        print(json.dumps({"status": "error", "message": "services[] must be a non-empty list"}))
        return 1

    required_services_raw = payload.get("required_services")
    required_services: Optional[Set[str]] = None
    if required_services_raw is not None:
        if not isinstance(required_services_raw, list) or not required_services_raw:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": "required_services must be a non-empty list when provided",
                    }
                )
            )
            return 1
        required_services = {str(item).strip() for item in required_services_raw if str(item).strip()}
        if not required_services:
            print(json.dumps({"status": "error", "message": "required_services cannot be empty"}))
            return 1

    seen: dict[str, str] = {}
    duplicates: list[str] = []
    invalid_owners: list[dict[str, str]] = []

    for row in services:
        if not isinstance(row, dict):
            print(json.dumps({"status": "error", "message": "each services[] item must be an object"}))
            return 1

        service = str(row.get("service", "")).strip()
        owner = str(row.get("owner", "")).strip()

        if not service:
            print(json.dumps({"status": "error", "message": "service id cannot be empty"}))
            return 1

        if service in seen:
            duplicates.append(service)
        else:
            seen[service] = owner

        if owner not in ALLOWED_OWNERS:
            invalid_owners.append({"service": service, "owner": owner})

    missing_required: list[str] = []
    unexpected_services: list[str] = []
    if required_services is not None:
        defined_services = set(seen.keys())
        missing_required = sorted(required_services - defined_services)
        unexpected_services = sorted(defined_services - required_services)

    if duplicates or invalid_owners or missing_required or unexpected_services:
        print(
            json.dumps(
                {
                    "status": "error",
                    "duplicates": sorted(set(duplicates)),
                    "invalid_owners": invalid_owners,
                    "missing_required": missing_required,
                    "unexpected_services": unexpected_services,
                },
                sort_keys=True,
            )
        )
        return 1

    counts = {"gws": 0, "ltr": 0}
    for owner in seen.values():
        counts[owner] += 1

    print(
        json.dumps(
            {
                "status": "success",
                "services": len(seen),
                "owner_counts": counts,
                "matrix": str(matrix_path.relative_to(repo_root)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
