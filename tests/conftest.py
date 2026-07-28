"""Shared pytest defaults for LiNKskills local proof."""

from __future__ import annotations

import os


# Trusted Eval Runner issuer material for unit/integration proof only.
os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)
os.environ.setdefault("LINKSKILLS_EVAL_RUNNER_ISSUER_ID", "linkskills-eval-runner-test")
# Unit tests may lack sandbox-exec/bwrap; certification still requires issuer HMAC.
os.environ.setdefault("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")
