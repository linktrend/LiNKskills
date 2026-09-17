# Remainder consumer inventory (read-only pinned sources)

Pinned identities:

| Repo | Ref | Commit | Tree |
| --- | --- | --- | --- |
| LiNKplatform | development | `358b2eb3b89c2809a94e1ad35c6d29d40d550d23` | `9c687688ef5cff0cd357dc5841e69c2abaad089f` |
| openclaw_prime | development | `f9c09dc53c8942b45b817e88fef49fe46bbc9d38` | `72ea598d5cb8b2156c8816a303ab1723f18d333e` |
| LiNKautowork | development | `20f3d4cc03445ca443e31c41f22d34347c866acf` | `95bec98a0d65ca30889e595a7bcaa85ddfe52b47` |
| IDE-Development | development | `65a28b7186635717988db6eeaed45cef28a7da1e` | `bce88bad5dee0958f00262e52ea2613d749055ff` |

## Findings

**Five OpenClaw Prime agents (Lisa, David, Eric, Sara, Jane):** Platform documents a production PACI *registration catalog of names* (`openclaw-<agent>-lskills`) in `docs/runbooks/production-identity-registration.md`. Live UUIDs, JWKs, and secret refs are HOLDs. That registration is concurrently owned — this packet does not interfere. OpenClaw Prime source at the pinned commit does not contain LiNKskills production bindings.

**LiNKautowork AI automations:** Product API has PACI *environment variable names* for its own API, not an observed production `lskills` PACI client or `provider_bindings` row.

**Codex / Cursor:** LiNKskills already has disabled ED-05 owner packets. No production PACI client proof. IDE Development does not mint PACI clients.

Skill retrieval alone must not create capability grants. Templates: `configs/consumer-activation/remainder-consumer-inventory.json` and `remainder-provider-bindings.template.json`.
