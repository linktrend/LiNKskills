"""Privacy-safe in-memory persistence; never retains rejected payload bodies."""
from __future__ import annotations
import hashlib
class MemoryStore:
    def __init__(self): self.releases={}; self.current={}; self.receipts={}; self.rejections=[]
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
