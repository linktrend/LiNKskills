# Catalog index

`index.json` is the machine-readable discovery surface for consumer Programs.

Certification state is **not** inferred from filesystem presence. Rebuild applies
an overlay from the honest classification ledger
(`evidence/phase10/skill-classification-draft.json`). A skill is `usable` only
when that ledger cites sealed live receipt evidence.

Regenerate after adding/removing/renaming skills **or** after certification:

```bash
# Structural catalog only (still applies ledger overlay when present):
python3 scripts/build-catalog-index.py
python3 scripts/build-catalog-index.py --check

# Sealed Linux/container batch certification (local Docker + bwrap; not stage):
./scripts/run-sealed-linux-certify.sh
```

See [`docs/LINKSKILLS-TECHNICAL-PRD.md`](../docs/LINKSKILLS-TECHNICAL-PRD.md) §6
(consumer load path) and [`docs/stage/CERTIFICATION-RUNTIME-READINESS.md`](../docs/stage/CERTIFICATION-RUNTIME-READINESS.md).
