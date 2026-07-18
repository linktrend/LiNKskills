# Catalog index

`index.json` is the machine-readable discovery surface for consumer Programs.
Regenerate after adding/removing/renaming skills:

```bash
python3 scripts/build-catalog-index.py
python3 scripts/build-catalog-index.py --check
```

See [`docs/CONSUMER-SKILL-LOAD-PATH.md`](../docs/CONSUMER-SKILL-LOAD-PATH.md).
