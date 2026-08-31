#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--route")
    args = parser.parse_args()
    data = json.loads((Path(__file__).resolve().parents[1] / "references" / "routing.json").read_text())
    if args.list:
        print(json.dumps({"routes": [r["route_id"] for r in data["routes"]]}, sort_keys=True))
        return 0
    if not args.route:
        parser.error("one of --list or --route is required")
    task = args.route.casefold()
    scored = []
    for route in data["routes"]:
        score = sum(1 for word in route["keywords"] if word.casefold() in task)
        if score:
            scored.append((score, route["route_id"], route["source_entrypoint"]))
    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored:
        result = {"status": "NOT_APPLICABLE", "selected_route": None, "source_entrypoint": None, "alternatives": []}
    elif len(scored) > 1 and scored[0][0] == scored[1][0]:
        result = {"status": "AMBIGUOUS", "selected_route": None, "source_entrypoint": None, "alternatives": [item[1] for item in scored if item[0] == scored[0][0]][:2]}
    else:
        result = {"status": "SELECTED", "selected_route": scored[0][1], "source_entrypoint": scored[0][2], "alternatives": []}
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
