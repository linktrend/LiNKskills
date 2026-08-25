# Old Patterns and Blacklist

- Writing transaction rows to a Supabase `lsl_finance` schema from a skill.
  - Resolution: return a review artifact; a separately owned system of record is outside scope.
- Treating GAAP-shaped tables as statutory or audit authority.
  - Resolution: label observations and route final authority to the qualified owner.
- Finalizing a close while a mismatch, stale snapshot, or missing source is unresolved.
  - Resolution: preserve the conflict and return `PENDING_APPROVAL`.
- Calling Odoo, Vault, or a direct API from a review primitive.
  - Resolution: require bounded consumer snapshots and an explicit empty-effects declaration.
- Treating urgency as approval or silently changing a source record.
  - Resolution: identify the owner and refuse the mutation.
