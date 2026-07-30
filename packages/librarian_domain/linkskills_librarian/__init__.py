"""LiNKskills Librarian domain worker package (contract v0.1)."""

from .conformance import DEFAULT_FIXTURES, FakeLibrarianHost
from .policies import FORBIDDEN_ACTIONS, PolicyDecision, evaluate_proposal
from .store import ReviewQueueStore, open_review_queue_store
from .worker import DOMAIN_KEY, WORKER_VERSION, DomainWorker

try:
    from .postgres_store import PostgresReviewQueueStore, open_postgres_review_queue_store
except ImportError:  # pragma: no cover — optional psycopg
    PostgresReviewQueueStore = None  # type: ignore[misc, assignment]
    open_postgres_review_queue_store = None  # type: ignore[misc, assignment]

__all__ = [
    "DEFAULT_FIXTURES",
    "DOMAIN_KEY",
    "FORBIDDEN_ACTIONS",
    "DomainWorker",
    "FakeLibrarianHost",
    "PolicyDecision",
    "PostgresReviewQueueStore",
    "ReviewQueueStore",
    "WORKER_VERSION",
    "evaluate_proposal",
    "open_postgres_review_queue_store",
    "open_review_queue_store",
]

__version__ = WORKER_VERSION
