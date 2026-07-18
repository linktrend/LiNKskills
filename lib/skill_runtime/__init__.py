"""LiNKskills consumer runtime: catalog index, skill loading, telemetry writers.

Programs that need skills should:
1. Check out / sync this repo (or sparse-checkout ``skills/`` + ``catalog/``).
2. Resolve skills via :mod:`lib.skill_runtime.catalog` / :mod:`lib.skill_runtime.loader`.
3. Record invocations via :mod:`lib.skill_runtime.telemetry`.

Permission-to-act is never decided here — that lives in each Program Ledger and
``platform.capability_grants`` (ADR 0001).
"""

from .catalog import CatalogEntry, build_catalog_index, load_catalog_index
from .loader import SkillBundle, load_skill, resolve_skill_path
from .telemetry import InvocationEvent, flush_telemetry_buffer, record_invocation

__all__ = [
    "CatalogEntry",
    "InvocationEvent",
    "SkillBundle",
    "build_catalog_index",
    "flush_telemetry_buffer",
    "load_catalog_index",
    "load_skill",
    "record_invocation",
    "resolve_skill_path",
]
