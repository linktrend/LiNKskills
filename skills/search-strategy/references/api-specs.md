# Tier Protocol Reference

Tier map (provider-neutral cost classes, not vendor APIs):
- `web`: low-cost baseline public retrieval.
- `neural`: technical similarity retrieval after a recorded confidence miss.
- `brief`: multi-step summarized reasoning.
- `social`: public sentiment context only.

Deep research policy:
- Any multi-step `brief` reasoning is HITL-gated.
- Must emit pre-action intent log and wait for `PROCEED`.

Facade policy:
- New broad workflows select canonical `research`.
- Never invoke `/tools/research` or name a retrieval vendor.
