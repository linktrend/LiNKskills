from __future__ import annotations

from .engine import LogicEngine


def run_retention_worker(engine: LogicEngine):
    return engine.run_retention_sweep()
