# Persistence v2 source HOLD

This package supplies source-level in-memory proofs only. Database migrations, RLS
application, backup/restore and production activation require the Platform operator.
Forward-fix by adding an additive versioned migration; do not rewrite release history.
