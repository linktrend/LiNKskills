#!/usr/bin/env python3
"""Validate canary-echo request shape and emit structured JSON."""

from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate canary-echo token/mode inputs and return structured JSON."
    )
    parser.add_argument("--input", required=True, help="Echo token to validate.")
    parser.add_argument(
        "--mode",
        choices=["plain", "json", "validate"],
        default="validate",
        help="Operation mode.",
    )
    args = parser.parse_args()
    token = str(args.input).strip()
    if not token:
        print(json.dumps({"status": "error", "message": "token must be non-empty"}))
        return 1
    print(
        json.dumps(
            {
                "status": "success",
                "processed_data": {"token": token, "mode": args.mode},
                "metadata": {"source": "helper_tool.py", "version": "0.2.0"},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
