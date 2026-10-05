# Output contract utility

Run `python3 scripts/helper_tool.py --artifact <authorized-output.json>` using the host-approved jsonschema dependency. It validates actual supplied output structure only and explicitly does not score behavior. Canonical `scripts/validate_skills.py` owns skill structure validation; no local duplicate validator. Upstream copied scripts are not executed.
