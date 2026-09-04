# Deterministic source-validation runner

Run `python3 scripts/helper_tool.py --run-suite`. The runner validates concrete inputs and exact outputs from `references/eval-suite.json`, checks reference integrity and empty effects, and writes nothing unless `--results PATH` is supplied. Any retained result is labeled `source_validation_only`, `uncertified`, `not_published`, and `selectable: false`.
