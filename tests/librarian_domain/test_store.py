#!/usr/bin/env python3
"""Librarian review queue persistence tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "librarian_domain"))

from linkskills_librarian.store import (  # noqa: E402
    InMemoryReviewQueueStore,
    SqliteReviewQueueStore,
    librarian_db_path,
)
from linkskills_librarian.worker import DomainWorker  # noqa: E402


class LibrarianStoreTests(unittest.TestCase):
    def test_sqlite_queue_persists_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SqliteReviewQueueStore(librarian_db_path(Path(tmp)))
            store.enqueue({"review_id": "r1", "kind": "general", "status": "queued", "at": "t"})
            self.assertEqual(store.depth(), 1)
            items = store.list_queue()
            self.assertEqual(items[0]["review_id"], "r1")
            store.close()

    def test_worker_uses_store_when_path_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = librarian_db_path(Path(tmp))
            worker = DomainWorker(store_path=str(db))
            result = worker.enqueue_review({"kind": "escalation"})
            self.assertEqual(result["queue_depth"], 1)
            self.assertTrue(db.is_file())


if __name__ == "__main__":
    unittest.main()
