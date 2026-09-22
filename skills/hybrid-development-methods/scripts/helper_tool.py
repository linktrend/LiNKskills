#!/usr/bin/env python3
"""Historical id: refuse to route. Named catalog skills are the working set."""
from __future__ import annotations
import json

print(
    json.dumps(
        {
            "status": "SUPERSEDED",
            "selected_route": None,
            "reason": "hybrid-development-methods is historical. Use named Software Development skills.",
            "ordinary_selectable": False,
        },
        sort_keys=True,
    )
)
