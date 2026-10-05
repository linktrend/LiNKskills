"""Inspect a supplied output artifact; never returns canned behavior PASS."""
import argparse, json, pathlib, sys
p=argparse.ArgumentParser()
p.add_argument("--artifact", required=True)
a=p.parse_args()
try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("jsonschema is unavailable; use the host-approved schema validator")
root=pathlib.Path(__file__).resolve().parents[1]
schema=json.loads((root/"references/schemas.json").read_text())["definitions"]["output"]
artifact=json.loads(pathlib.Path(a.artifact).read_text())
errors=[e.message for e in Draft202012Validator(schema).iter_errors(artifact)]
print(json.dumps({"kind":"output_contract_only", "valid":not errors,"errors":errors,
"behavioral_quality":"not_evaluated", "skill":root.name}))
sys.exit(1 if errors else 0)
