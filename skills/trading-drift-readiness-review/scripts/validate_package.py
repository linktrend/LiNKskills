#!/usr/bin/env python3
"""Check draft package structure, JSON syntax, and non-circular file-manifest hashes only."""
import hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
required=[root/"SKILL.md",root/"references/schemas.json",root/"references/skill-pack.json",root/"references/execution-profile.json",root/"references/eval-suite.json",root/"references/eval-suite.yaml",root/"references/source-provenance.json",root/"references/hash-manifest.json",root/"scripts/helper_tool.py",root/"scripts/README.md"]
for path in required:
    if not path.is_file(): raise SystemExit(f"missing required file: {path.relative_to(root)}")
for path in root.rglob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))
text=(root/"SKILL.md").read_text(encoding="utf-8")
for section in ["# ","## Use when","## Inputs","## Outputs","## Rules","## Decision path","## Evidence standard","## Blocker standard","## Workflow","## Tool protocol and persistence","## Contract pointers"]:
    if section not in text: raise SystemExit(f"missing section: {section}")
if "## Method" not in text and "## Integrated method" not in text: raise SystemExit("missing method section")
profile=json.loads((root/"references/execution-profile.json").read_text())
if profile.get("certification",{}).get("status") != "uncertified": raise SystemExit("draft must remain uncertified")
if profile.get("lifecycle_state") != "draft": raise SystemExit("draft lifecycle mismatch")
suite=json.loads((root/"references/eval-suite.json").read_text())
if suite.get("skill_id") != root.name or suite.get("pass_threshold") is None or not suite.get("cases"): raise SystemExit("canonical eval draft is incomplete")
if suite.get("schema_version") != "0.1": raise SystemExit("unexpected eval schema version")
pack=json.loads((root/"references/skill-pack.json").read_text())
if pack.get("lifecycle_state") != "draft" or pack.get("eval",{}).get("suite_path") != "references/eval-suite.json": raise SystemExit("draft Skill Pack metadata mismatch")
manifest=json.loads((root/"references/hash-manifest.json").read_text())
for rel, expected in manifest["files"].items():
    path=(root/rel).resolve()
    if root.resolve() not in path.parents or not path.is_file(): raise SystemExit(f"invalid manifest path: {rel}")
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected: raise SystemExit(f"hash mismatch: {rel}")
if "references/execution-profile.json" in manifest["files"]: raise SystemExit("manifest must exclude profile to avoid hash cycle; profile carries canonical self-identity")
print("PACKAGE_STRUCTURE_AND_LOCAL_MANIFEST_OK; canonical validator and behavior qualification are separate")
