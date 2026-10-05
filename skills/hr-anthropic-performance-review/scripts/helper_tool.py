#!/usr/bin/env python3
"""Offline, value-redacting envelope presence check; no HR actions or file writes."""
import json, sys
REQUIRED = ("task_ref", "request_ref", "source_refs", "data_classification", "task_inputs", "decision_owner_role")
def main():
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(json.dumps({"status":"FAILED","reason":"invalid_json","external_effects":[],"mutations":[]}))
        return 2
    if not isinstance(value, dict):
        print(json.dumps({"status":"FAILED","reason":"expected_object","external_effects":[],"mutations":[]}))
        return 2
    missing = sorted(k for k in REQUIRED if k not in value or value[k] in (None, "", []))
    print(json.dumps({"status":"NEEDS_CONTEXT" if missing else "ENVELOPE_PRESENT","missing_fields":missing,"value_echo":False,"external_effects":[],"mutations":[]}, sort_keys=True))
    return 3 if missing else 0
if __name__ == "__main__":
    sys.exit(main())
