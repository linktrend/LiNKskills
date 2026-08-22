#!/usr/bin/env python3
"""Emit a deterministic planning checkpoint envelope from JSON input."""
import json
import sys

payload = json.load(sys.stdin)
print(json.dumps({"status": "INITIALIZED", "request_keys": sorted(payload)}, separators=(",", ":")))
