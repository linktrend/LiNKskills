#!/usr/bin/env python3
"""Emit a deterministic report initialization envelope from JSON input."""
import json
import sys

payload = json.load(sys.stdin)
print(json.dumps({"status": "INITIALIZED", "mode": payload.get("mode"), "source_count": len(payload.get("sources", []))}, separators=(",", ":")))
