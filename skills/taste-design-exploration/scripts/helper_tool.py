#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--route")
    parser.add_argument("--route-id")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "references" / "routing.json").read_text())
    admission_doc = json.loads((root / "references" / "admission.json").read_text())
    admission = {item["route_id"]: item for item in admission_doc["members"]}
    routes = {item["route_id"]: item for item in data["routes"]}
    if args.list:
        print(json.dumps({"routes": [{"route_id": route_id, "admission_state": admission[route_id]["admission_state"], "routing_allowed": admission[route_id]["routing_allowed"]} for route_id in sorted(routes)]}, sort_keys=True))
        return 0
    if bool(args.route) == bool(args.route_id):
        parser.error("exactly one of --list, --route, or --route-id is required")
    if args.route_id:
        route = routes.get(args.route_id)
        if route is None:
            result = {"status": "NOT_APPLICABLE", "selected_route": None, "source_entrypoint": None, "release_id": None, "admission_state": None, "ordinary_selectable": False, "alternatives": [], "reason": "unknown route id"}
        else:
            scored = [(1, route["route_id"], route["source_entrypoint"])]
    else:
        task = args.route.casefold()
        scored = []
        for route in data["routes"]:
            score = sum(1 for word in route["keywords"] if word.casefold() in task)
            if score:
                scored.append((score, route["route_id"], route["source_entrypoint"]))
        scored.sort(key=lambda item: (-item[0], item[1]))
    if 'result' not in locals():
        if not scored:
            result = {"status": "NOT_APPLICABLE", "selected_route": None, "source_entrypoint": None, "release_id": None, "admission_state": None, "ordinary_selectable": False, "alternatives": [], "reason": "no route matched"}
        elif len(scored) > 1 and scored[0][0] == scored[1][0]:
            result = {"status": "AMBIGUOUS", "selected_route": None, "source_entrypoint": None, "release_id": None, "admission_state": None, "ordinary_selectable": False, "alternatives": [item[1] for item in scored if item[0] == scored[0][0]][:2], "reason": "top routes tied"}
        else:
            selected = scored[0]
            gate = admission[selected[1]]
            if not gate["routing_allowed"]:
                result = {"status": "NOT_ELIGIBLE", "selected_route": selected[1], "source_entrypoint": None, "release_id": gate["release_id"], "admission_state": gate["admission_state"], "ordinary_selectable": False, "alternatives": [], "reason": "member is not approved for internal canary routing"}
            else:
                result = {"status": "SELECTED", "selected_route": selected[1], "source_entrypoint": selected[2], "release_id": gate["release_id"], "admission_state": gate["admission_state"], "ordinary_selectable": False, "alternatives": [], "reason": "one approved internal-canary route matched"}
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
