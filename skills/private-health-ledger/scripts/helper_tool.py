#!/usr/bin/env python3
"""Emit a deterministic redaction envelope from a health result request."""
import json
import sys

payload = json.load(sys.stdin)
print(json.dumps({"status": "INITIALIZED", "private_fields_present": bool(payload.get("observations")), "capacity_only": True}, separators=(",", ":")))
