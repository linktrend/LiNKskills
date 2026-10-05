# Synthetic success pattern

Request: A supplied register snapshot has open, in-progress and closed records, one item with resolution evidence, and one proposed risk acceptance without a named authorized acceptor.

Expected: report snapshot status, prepare closure only where evidence is supplied, leave risk acceptance unresolved without an authorized acceptor, and return owner questions. No intake, notices, record writes or external effects.
