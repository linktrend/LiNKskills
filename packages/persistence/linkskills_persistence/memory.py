"""Privacy-safe in-memory persistence; never retains rejected payload bodies."""
from __future__ import annotations
import hashlib
class MemoryStore:
    """Small source-only store for immutable lifecycle records.

    This adapter intentionally has no migration/apply capability.  It is useful
    for deterministic unit proofs and can be replaced by the Platform-owned
    Postgres adapter without changing lifecycle contracts.
    """

    def __init__(self):
        self.releases={}; self.current={}; self.receipts={}; self.rejections=[]
        self.vendor_releases={}; self.adaptations={}; self.collections={}
        self.candidates={}; self.candidate_keys={}; self.reviews={}; self.pointer_history=[]
    def put_release(self, org, release, record):
        key=(org,release)
        if key in self.releases: raise ValueError("immutable_release")
        self.releases[key]=dict(record)
    def get_release(self, org, release):
        if (org,release) not in self.releases: raise ValueError("not_found")
        return dict(self.releases[(org,release)])
    def cas_current(self, org, skill, expected, version):
        key=(org,skill)
        if self.current.get(key)!=expected: raise ValueError("cas_conflict")
        self.current[key]=version
    def receipt(self, org, key, digest):
        existing=self.receipts.get((org,key))
        if existing and existing["digest"]!=digest: raise ValueError("idempotency_conflict")
        return self.receipts.setdefault((org,key), {"digest":digest,"receipt_id":digest[:24]})
    def reject(self, body: bytes, reason: str):
        self.rejections.append({"reason":reason,"byte_size":len(body),"digest":"sha256:"+hashlib.sha256(body).hexdigest()})

    def put_vendor_release(self, org, release_id, record):
        """Persist an immutable vendor release record exactly once."""
        key=(org,release_id); value=dict(record)
        existing=self.vendor_releases.get(key)
        if existing is not None and existing != value: raise ValueError("immutable_vendor_release")
        self.vendor_releases.setdefault(key, value)
        return dict(self.vendor_releases[key])

    def put_adaptation(self, org, release_id, record):
        """Persist a linked adaptation without modifying its vendor parent."""
        key=(org,release_id); value=dict(record)
        existing=self.adaptations.get(key)
        if existing is not None and existing != value: raise ValueError("immutable_adaptation")
        self.adaptations.setdefault(key, value)
        return dict(self.adaptations[key])

    def put_candidate(self, org, idempotency_key, candidate):
        """Store a candidate idempotently and reject conflicting replays."""
        key=(org,idempotency_key); value=dict(candidate)
        existing_id=self.candidate_keys.get(key)
        if existing_id is not None:
            existing=self.candidates[(org,existing_id)]
            if existing.get("candidate_digest") != value.get("candidate_digest"):
                raise ValueError("idempotency_conflict")
            return dict(existing)
        candidate_id=str(value.get("candidate_id") or "")
        if not candidate_id: raise ValueError("missing_candidate_id")
        self.candidate_keys[key]=candidate_id
        self.candidates[(org,candidate_id)]=value
        return dict(value)

    def put_review(self, org, review_id, review):
        """Persist one immutable Librarian outcome."""
        key=(org,review_id); value=dict(review)
        existing=self.reviews.get(key)
        if existing is not None and existing != value: raise ValueError("immutable_review")
        self.reviews.setdefault(key, value)
        return dict(self.reviews[key])

    def apply_platform_receipt(self, org, collection_id, target_release_id, *, expected_current, receipt):
        """Move a pointer only after a matching Platform apply receipt."""
        data=dict(receipt)
        if data.get("authority") != "LiNKplatform" or not data.get("applied"):
            raise ValueError("platform_apply_receipt_required")
        if data.get("operation") == "rollback":
            raise ValueError("apply_receipt_operation_invalid")
        if data.get("operation") not in (None, "apply"):
            raise ValueError("apply_receipt_operation_invalid")
        data["operation"] = "apply"
        if data.get("collection_id") not in (None, collection_id):
            raise ValueError("apply_collection_mismatch")
        record = self.vendor_releases.get((org, target_release_id)) or self.adaptations.get((org, target_release_id))
        if record is not None and record.get("collection_id") not in (None, collection_id):
            raise ValueError("apply_release_collection_mismatch")
        data.update({"collection_id": collection_id, "release_id": target_release_id, "operation": "apply"})
        existing_receipt = self.receipts.get((org, str(data.get("receipt_id") or "")))
        if existing_receipt is not None:
            if existing_receipt != data:
                raise ValueError("platform_receipt_conflict")
            return dict(existing_receipt)
        key=(org,collection_id); current=self.current.get(key)
        if current != expected_current: raise ValueError("cas_conflict")
        self.current[key]=target_release_id
        self.receipts[(org,str(data.get("receipt_id") or ""))]=data
        self.pointer_history.append({"org":org,"collection_id":collection_id,"from":current,"to":target_release_id,"receipt_id":data.get("receipt_id")})
        return dict(data)

    def get_current(self, org, collection_id):
        """Read a collection pointer without fallback selection."""
        return self.current.get((org,collection_id))
