"""Postgres-backed v2 runtime; publication and activation stay operator-owned."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from linkskills_core.mcp_v2 import release_resource_uri
from linkskills_core.provider_v2 import PROTOCOL_VERSION, RESOURCE_OPERATIONS, V2Provider, WRITE_TOOLS, _normalize_release


def _aisle(aisle_id: str, display_name: str, description: str) -> dict[str, str]:
    return {
        "subcategory_id": aisle_id,
        "display_name": display_name,
        "description": description,
    }


def _floor(
    family_id: str,
    display_name: str,
    description: str,
    aisles: tuple[dict[str, str], ...] = (),
) -> dict[str, Any]:
    return {
        "family_id": family_id,
        "display_name": display_name,
        "description": description,
        "subcategories": aisles,
    }


_EMPTY_PROGRAM = "Empty until it has a skill or note of its own."

# Floors and aisles. Generic descriptions name the work, not a person or company.
# Trading stays empty. Program floors point at a shared floor and hold no skill of their own.
CATALOG_FLOORS: tuple[dict[str, Any], ...] = (
    _floor(
        "operations",
        "Operations",
        "Business plans, branding, office tools, workforce, meetings, incidents, and reporting.",
        (
            _aisle("workforce", "Workforce", "Roles, blockers, coordination, and health reporting."),
            _aisle(
                "company",
                "Company",
                "Plans, decisions, meetings, time, incidents, and communication.",
            ),
            _aisle("office", "Office", "Office workspace tasks."),
            _aisle("improvement", "Improvement", "Review of how skills and tools are used."),
        ),
    ),
    _floor(
        "finance",
        "Finance",
        "Accounting, close review, and revenue records.",
        (
            _aisle("accounting", "Accounting", "Cash, budget, and invoice records."),
            _aisle("close", "Close review", "Close review and variance checks."),
            _aisle("revenue", "Revenue", "Revenue records."),
        ),
    ),
    _floor(
        "company-legal-and-records",
        "Company legal and records",
        "Contracts, vendors, files, and the record of intent before a write.",
        (
            _aisle("contracts", "Contracts", "Contracts."),
            _aisle("vendors", "Vendors", "Vendors and suppliers."),
            _aisle("files", "Files", "Files and archives."),
            _aisle("intent", "Intent", "The record of intent before a write."),
        ),
    ),
    _floor(
        "customers-and-marketing",
        "Customers and Marketing",
        "Marketing, channels, creative production, sales, and publish-time compliance.",
        (
            _aisle("marketing", "Marketing", "Marketing strategy and search."),
            _aisle("channels", "Channels", "Channel operations."),
            _aisle("creative", "Creative", "Creative production."),
            _aisle("sales", "Sales", "Sales and customers."),
            _aisle("compliance", "Compliance", "Publish-time compliance."),
        ),
    ),
    _floor("product", "Product", "Product definition and portfolio."),
    _floor(
        "research",
        "Research",
        "How research is done, cited, searched, and how markets and targets are assessed.",
        (
            _aisle("method", "Method", "How research is done, cited, and searched."),
            _aisle("markets", "Markets", "Market assessment."),
            _aisle("targets", "Targets", "Target definition and assessment."),
        ),
    ),
    _floor("trading", "Trading", "Trading strategy, risk, and performance."),
    _floor(
        "software-development",
        "Software Development",
        "Design and coding.",
        (
            _aisle("design", "Design", "Interface design."),
            _aisle("coding", "Coding", "Software construction and delivery."),
        ),
    ),
    _floor("linkdeveloper", "LiNKdeveloper", "Points at Software Development, Coding."),
    _floor(
        "linkresearch",
        "LiNKresearch",
        "Points at Research. Jane operates this program.",
    ),
    _floor("linksites", "LiNKsites", _EMPTY_PROGRAM),
    _floor("linktarget", "LiNKtarget", _EMPTY_PROGRAM),
    _floor("linksales", "LiNKsales", _EMPTY_PROGRAM),
    _floor("linkclient", "LiNKclient", _EMPTY_PROGRAM),
    _floor("linkeditorial", "LiNKeditorial", _EMPTY_PROGRAM),
    _floor("linkcontent", "LiNKcontent", _EMPTY_PROGRAM),
    _floor("linkpublish", "LiNKpublish", _EMPTY_PROGRAM),
    _floor("linkchannel", "LiNKchannel", _EMPTY_PROGRAM),
    _floor("linkcampaign", "LiNKcampaign", _EMPTY_PROGRAM),
    _floor("linktrading", "LiNKtrading", "Empty. May point at Trading and at Research."),
    _floor(
        "linklegal",
        "LiNKlegal",
        "Jane operates this program. It points at Company legal and records only when a skill is shared.",
    ),
    _floor(
        "systems",
        "Systems",
        "How to use each system. How to build one stays on Software Development.",
        tuple(
            _aisle(aisle_id, display_name, "How to use this system.")
            for aisle_id, display_name in (
                ("linkharness", "LiNKharness"),
                ("linkprofiles", "LiNKprofiles"),
                ("linkplatform", "LiNKplatform"),
                ("linkskills", "LiNKskills"),
                ("linkbrain", "LiNKbrain"),
                ("linkautowork", "LiNKautowork"),
                ("linklibraries", "LiNKlibraries"),
                ("openclaw", "OpenClaw"),
                ("linkconsole", "LiNKconsole"),
                ("linkportal", "LiNKportal"),
            )
        ),
    ),
)

# skill_id -> (floor, aisle). Left off shared floors:
# private-health-wellbeing, personal-compliance.
CATALOG_PLACEMENTS: dict[str, tuple[str, str]] = {
    "agent-workforce-management": ("operations", "workforce"),
    "blocker-resolution": ("operations", "workforce"),
    "department-head": ("operations", "workforce"),
    "executive-sync-8am": ("operations", "workforce"),
    "studio-health-reporting": ("operations", "workforce"),
    "company-planning-performance": ("operations", "company"),
    "executive-decisions-governance": ("operations", "company"),
    "meeting-management": ("operations", "company"),
    "time-management": ("operations", "company"),
    "operational-reporting": ("operations", "company"),
    "company-incident-continuity": ("operations", "company"),
    "company-communication": ("operations", "company"),
    "google-workspace-operations": ("operations", "office"),
    "self-improvement": ("operations", "improvement"),
    "finance-accounting-operations": ("finance", "accounting"),
    "studio-controller": ("finance", "close"),
    "revenue-adapter-base": ("finance", "revenue"),
    "commercial-contracts-legal-operations": ("company-legal-and-records", "contracts"),
    "procurement-vendor-management": ("company-legal-and-records", "vendors"),
    "smart-file-clerk": ("company-legal-and-records", "files"),
    "audit-protocol": ("company-legal-and-records", "intent"),
    "marketing-strategist": ("customers-and-marketing", "marketing"),
    "engagement-to-strategy-loop": ("customers-and-marketing", "marketing"),
    "seo-semantic-auditor": ("customers-and-marketing", "marketing"),
    "channel-ops": ("customers-and-marketing", "channels"),
    "creative-director": ("customers-and-marketing", "creative"),
    "creative-qa": ("customers-and-marketing", "creative"),
    "sales-customer-management": ("customers-and-marketing", "sales"),
    "compliance-guardian": ("customers-and-marketing", "compliance"),
    "research": ("research", "method"),
    "search-strategy": ("research", "method"),
    "citation-enforcer": ("research", "method"),
    "market-analyst": ("research", "markets"),
    "target-definition-segmentation": ("research", "targets"),
    "target-assessment-prioritization": ("research", "targets"),
    "awesome-design-presets": ("software-development", "design"),
    "emil-design-engineering": ("software-development", "design"),
    "impeccable-design-system": ("software-development", "design"),
    "taste-design-exploration": ("software-development", "design"),
    "ui-ux-guardian": ("software-development", "design"),
    "git-safeguard": ("software-development", "coding"),
    "persistent-qa": ("software-development", "coding"),
    "repository-manager": ("software-development", "coding"),
    "skill-template": ("software-development", "coding"),
    "tool-architect": ("software-development", "coding"),
    "prd-architect": ("software-development", "coding"),
    "software-pm": ("software-development", "coding"),
    "lead-engineer": ("software-development", "coding"),
    "studio-architect": ("software-development", "coding"),
    "task-decomposition": ("software-development", "coding"),
    "self-critique-loop": ("software-development", "coding"),
    "skill-architect": ("software-development", "coding"),
    "devops-sre": ("software-development", "coding"),
    "workflow-architect": ("software-development", "coding"),
    "governed-browser-use": ("software-development", "coding"),
    "canary-echo": ("software-development", "coding"),
    "triage": ("software-development", "coding"),
    "grill-office-hours": ("software-development", "coding"),
    "to-questionnaire": ("software-development", "coding"),
    "plan-ceo-review": ("software-development", "coding"),
    "writing-for-agents": ("software-development", "coding"),
    "technical-prd": ("software-development", "coding"),
    "autoplan": ("software-development", "coding"),
    "to-tickets": ("software-development", "coding"),
    "gap-design": ("software-development", "coding"),
    "plan-eng-review": ("software-development", "coding"),
    "implement": ("software-development", "coding"),
    "phase-review": ("software-development", "coding"),
    "diagnose-investigate": ("software-development", "coding"),
    "cso": ("software-development", "coding"),
    "qa-only": ("software-development", "coding"),
    "devex-review": ("software-development", "coding"),
    "benchmark": ("software-development", "coding"),
    "design-html": ("software-development", "coding"),
    "ship": ("software-development", "coding"),
    "land-and-deploy": ("software-development", "coding"),
    "canary": ("software-development", "coding"),
    "document-release": ("software-development", "coding"),
    "design-sample": ("software-development", "design"),
    "pick-ui-library": ("software-development", "design"),
    "mobile-native-web": ("software-development", "design"),
    "ask-sonner": ("software-development", "design"),
    "redesign-existing-ui": ("software-development", "design"),
}

UNFILED_SKILL_IDS = frozenset({
    "private-health-wellbeing",
    "personal-compliance",
})


def catalog_families(releases: list[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Return the filed floors. Release family ids do not add another floor."""
    del releases
    return [
        {
            "family_id": floor["family_id"],
            "display_name": floor["display_name"],
            "description": floor["description"],
            "subcategories": tuple(floor["subcategories"]),
        }
        for floor in CATALOG_FLOORS
    ]


def catalog_index_path() -> Path | None:
    """Find the gateway catalog index without preferring a missing install path."""
    candidates: list[Path] = []
    env = os.environ.get("LINKSKILLS_REPO_ROOT", "").strip()
    if env:
        candidates.append(Path(env) / "catalog" / "index.json")
    candidates.append(Path("/opt/linkskills/catalog/index.json"))
    here = Path(__file__).resolve()
    candidates.extend(parent / "catalog" / "index.json" for parent in here.parents)
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_catalog_entries() -> list[dict[str, str]]:
    """Read skill ids from the gateway catalog. Missing index means no drafts to file."""
    path = catalog_index_path()
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries: list[dict[str, str]] = []
    for raw in payload.get("skills", []):
        if not isinstance(raw, Mapping) or not raw.get("skill_id"):
            continue
        entries.append(
            {
                "skill_id": str(raw["skill_id"]),
                "version": str(raw.get("version") or "0.0.0"),
                "certification_state": str(raw.get("certification_state") or "draft"),
            }
        )
    return entries


def filed_releases(qualified: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Place catalog skills on floors. Qualified releases stay qualified."""
    filed: list[dict[str, Any]] = []
    seen: set[str] = set()
    for release in qualified:
        skill_id = str(release.get("skill_id") or "")
        updated = dict(release)
        placement = CATALOG_PLACEMENTS.get(skill_id)
        if placement:
            updated["family_id"] = placement[0]
            updated["subcategory_id"] = placement[1]
        if skill_id:
            seen.add(skill_id)
        filed.append(updated)
    for entry in load_catalog_entries():
        skill_id = entry["skill_id"]
        if skill_id in seen or skill_id not in CATALOG_PLACEMENTS:
            continue
        family_id, subcategory_id = CATALOG_PLACEMENTS[skill_id]
        seen.add(skill_id)
        filed.append(
            {
                "skill_id": skill_id,
                "version": entry["version"],
                "family_id": family_id,
                "subcategory_id": subcategory_id,
                "lifecycle_state": entry["certification_state"],
                "qualification": "draft",
                "resources": {},
            }
        )
    return filed



def manifest_digest(value: Mapping[str, Any]) -> str:
    """Hash the immutable JSON publication document, including resource digests."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def decode_release(row: Mapping[str, Any], resource_ids: set[str] | None = None) -> dict[str, Any]:
    """Reject corrupted or unqualified publication records before serving bytes."""
    manifest = row["manifest"]
    if not isinstance(manifest, dict) or manifest_digest(manifest) != row["manifest_sha256"]:
        raise ValueError("integrity_mismatch")
    if manifest.get("qualification") != "qualified":
        raise ValueError("not_qualified")
    if row["release_id"] != f"{manifest.get('skill_id')}@{manifest.get('version')}":
        raise ValueError("integrity_mismatch")
    release = dict(manifest)
    resources = {}
    for name, resource in manifest.get("resources", {}).items():
        if resource_ids is not None and name not in resource_ids:
            continue
        body = base64.b64decode(resource["content_b64"], validate=True)
        if "sha256:" + hashlib.sha256(body).hexdigest() != resource["content_digest"]:
            raise ValueError("integrity_mismatch")
        resources[name] = {**resource, "body": body}
    if not resources:
        raise ValueError("not_found" if resource_ids is not None else "catalog_unavailable")
    release["resources"] = resources
    release["lifecycle_state"] = row["lifecycle"]
    return release


def decode_split_release(
    row: Mapping[str, Any], resources: list[Mapping[str, Any]], resource_ids: set[str] | None = None
) -> dict[str, Any]:
    """Decode a release whose resource bytes are stored in bounded rows."""
    manifest = row["manifest"]
    if not isinstance(manifest, dict) or row["release_id"] != f"{manifest.get('skill_id')}@{manifest.get('version')}":
        raise ValueError("integrity_mismatch")
    if manifest.get("qualification") != "qualified":
        raise ValueError("not_qualified")
    if manifest_digest(manifest) != row.get("manifest_sha256"):
        raise ValueError("integrity_mismatch")
    manifest_resources = manifest.get("resources")
    if not isinstance(manifest_resources, dict):
        raise ValueError("integrity_mismatch")
    release = dict(manifest)
    decoded: dict[str, Any] = {}
    for resource in resources:
        name = str(resource["resource_id"])
        if resource_ids is not None and name not in resource_ids:
            continue
        body = bytes(resource["content"])
        if "sha256:" + hashlib.sha256(body).hexdigest() != resource["content_digest"]:
            raise ValueError("integrity_mismatch")
        descriptor = manifest_resources.get(name)
        if not isinstance(descriptor, dict) or descriptor.get("content_digest") != resource["content_digest"]:
            raise ValueError("integrity_mismatch")
        if descriptor.get("media_type", "text/markdown") != resource["media_type"]:
            raise ValueError("integrity_mismatch")
        if descriptor.get("byte_size") is not None and int(descriptor["byte_size"]) != len(body):
            raise ValueError("integrity_mismatch")
        decoded[name] = {
            **descriptor,
            "content_b64": base64.b64encode(body).decode("ascii"),
            "body": body,
        }
    if not decoded:
        raise ValueError("not_found" if resource_ids is not None else "catalog_unavailable")
    release["resources"] = decoded
    release["lifecycle_state"] = row["lifecycle"]
    return release


class PostgresProviderStore:
    """Open bounded transactions with verified actor/org identity and a fixed role."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    @contextmanager
    def transaction(self, *, org_id: str = "", actor_id: str = ""):
        """Never accept a caller-selected SQL role or expose connection errors."""
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self._dsn, row_factory=dict_row, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("set local role svc_lskills_runtime")
                cur.execute("set local statement_timeout = '5s'")
                cur.execute("select set_config('app.current_org_id', %s, true)", (org_id,))
                cur.execute("select set_config('app.current_actor_id', %s, true)", (actor_id,))
                yield cur

    def probe(self) -> Mapping[str, Any]:
        """Verify all three runtime tables are reachable under the runtime role."""
        with self.transaction() as cur:
            for table in ("provider_releases", "provider_bindings", "provider_receipts"):
                cur.execute(f"select 1 from lskills.{table} limit 1")
        return {"ready": True, "code": "store_ready"}

    def snapshot(self, claims: Any) -> tuple[list[dict[str, Any]], Mapping[str, Any]]:
        """Refresh revocation and exact consumer activation on every request."""
        with self.transaction(org_id=claims.org_id, actor_id=claims.actor_id) as cur:
            cur.execute(
                "select runtime_profile, release_ids from lskills.provider_bindings "
                "where org_id=%s and actor_id=%s and runtime_binding_id=%s and enabled",
                (claims.org_id, claims.actor_id, claims.runtime_binding_id),
            )
            binding = cur.fetchone()
            if not binding or not binding["release_ids"]:
                raise ValueError("forbidden")
            cur.execute(
                "select release_id, manifest, manifest_sha256, lifecycle "
                "from lskills.provider_releases where release_id = any(%s) order by release_id",
                (binding["release_ids"],),
            )
            releases = [decode_release(row) for row in cur.fetchall()]
            if {f"{r['skill_id']}@{r['version']}" for r in releases} != set(binding["release_ids"]):
                raise ValueError("catalog_unavailable")
        return releases, binding

    def snapshot_metadata(self, claims: Any) -> tuple[list[dict[str, Any]], Mapping[str, Any]]:
        """Return bounded release metadata without decoding embedded resource bytes."""
        with self.transaction(org_id=claims.org_id, actor_id=claims.actor_id) as cur:
            cur.execute(
                "select runtime_profile, release_ids from lskills.provider_bindings "
                "where org_id=%s and actor_id=%s and runtime_binding_id=%s and enabled",
                (claims.org_id, claims.actor_id, claims.runtime_binding_id),
            )
            binding = cur.fetchone()
            if not binding or not binding["release_ids"]:
                raise ValueError("forbidden")
            # JSONB subtraction leaves all release metadata intact while removing
            # the potentially very large resource bodies from the result.
            cur.execute(
                "select release_id, manifest - 'resources' as manifest, manifest_sha256, lifecycle "
                "from lskills.provider_releases where release_id = any(%s) order by release_id",
                (binding["release_ids"],),
            )
            rows = []
            for row in cur.fetchall():
                manifest = row["manifest"]
                if not isinstance(manifest, dict) or row["release_id"] != f"{manifest.get('skill_id')}@{manifest.get('version')}":
                    raise ValueError("integrity_mismatch")
                release = dict(manifest)
                if manifest.get("qualification") != "qualified":
                    raise ValueError("not_qualified")
                release["lifecycle_state"] = row["lifecycle"]
                release["release_id"] = row["release_id"]
                rows.append(release)
            if {r["release_id"] for r in rows} != set(binding["release_ids"]):
                raise ValueError("catalog_unavailable")
            return rows, binding

    def fetch_release(self, claims: Any, release_id: str, resource_ids: set[str] | None = None) -> dict[str, Any]:
        """Fetch one authorized release; unrelated bound release bodies stay untouched."""
        with self.transaction(org_id=claims.org_id, actor_id=claims.actor_id) as cur:
            cur.execute(
                "select runtime_profile, release_ids from lskills.provider_bindings "
                "where org_id=%s and actor_id=%s and runtime_binding_id=%s and enabled",
                (claims.org_id, claims.actor_id, claims.runtime_binding_id),
            )
            binding = cur.fetchone()
            if not binding or release_id not in set(binding["release_ids"]):
                raise ValueError("forbidden")
            cur.execute(
                "select release_id, manifest, manifest_sha256, lifecycle "
                "from lskills.provider_releases where release_id=%s",
                (release_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("not_found")
            # New publications keep bytes in bounded rows. Existing publications
            # retain the embedded-manifest fallback for immutable compatibility.
            cur.execute("select to_regclass('lskills.provider_release_resources') as table_name")
            resource_table_present = bool(cur.fetchone()["table_name"])
            if not resource_table_present and (row["manifest"] or {}).get("resource_storage") == "separate_rows_v1":
                raise ValueError("store_unavailable")
            if resource_table_present:
                if resource_ids is None:
                    cur.execute(
                        "select resource_id, content_digest, media_type, content "
                        "from lskills.provider_release_resources where release_id=%s order by resource_id",
                        (release_id,),
                    )
                else:
                    cur.execute(
                        "select resource_id, content_digest, media_type, content "
                        "from lskills.provider_release_resources "
                        "where release_id=%s and resource_id = any(%s) order by resource_id",
                        (release_id, list(resource_ids)),
                    )
                resource_rows = cur.fetchall()
                if resource_rows:
                    row = dict(row)
                    row["decoded_release"] = decode_split_release(row, resource_rows, resource_ids)
                elif (row["manifest"] or {}).get("resource_storage") == "separate_rows_v1":
                    raise ValueError("not_found")
            return {"row": row, "binding": binding}

    def fetch_release_metadata(self, claims: Any, release_id: str) -> dict[str, Any]:
        """Fetch one release's descriptors without selecting resource bytes."""
        with self.transaction(org_id=claims.org_id, actor_id=claims.actor_id) as cur:
            cur.execute(
                "select runtime_profile, release_ids from lskills.provider_bindings "
                "where org_id=%s and actor_id=%s and runtime_binding_id=%s and enabled",
                (claims.org_id, claims.actor_id, claims.runtime_binding_id),
            )
            binding = cur.fetchone()
            if not binding or release_id not in set(binding["release_ids"]):
                raise ValueError("forbidden")
            cur.execute(
                "select release_id, case when exists (select 1 from jsonb_each(manifest->'resources') r where r.value ? 'content_b64') "
                "then manifest else manifest - 'resources' || jsonb_build_object('resources', "
                "coalesce((select jsonb_object_agg(key, value - 'content_b64') from jsonb_each(manifest->'resources')), '{}'::jsonb)) end as manifest, "
                "manifest_sha256, lifecycle, "
                "exists (select 1 from jsonb_each(manifest->'resources') r where r.value ? 'content_b64') as embedded_resources "
                "from lskills.provider_releases where release_id=%s",
                (release_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("not_found")
            manifest = row["manifest"]
            if row["release_id"] != f"{manifest.get('skill_id')}@{manifest.get('version')}" or manifest_digest(manifest) != row["manifest_sha256"]:
                raise ValueError("integrity_mismatch")
            if manifest.get("qualification") != "qualified" or row["lifecycle"] != "qualified":
                raise ValueError("not_qualified")
            return {"row": row, "binding": binding}

    def get(self, kind: str, receipt_id: str, *, org_id: str, actor_id: str):
        """Read a receipt only within the authenticated actor's organization."""
        with self.transaction(org_id=org_id, actor_id=actor_id) as cur:
            cur.execute(
                "select record from lskills.provider_receipts "
                "where org_id=%s and actor_id=%s and kind=%s and receipt_id=%s",
                (org_id, actor_id, kind, receipt_id),
            )
            row = cur.fetchone()
            return row["record"] if row else None

    def put(self, kind: str, receipt_id: str, record: Mapping[str, Any], *, org_id: str, actor_id: str):
        """Insert once; concurrent retries replay and conflicting payloads fail."""
        from psycopg.types.json import Jsonb

        if not org_id or not actor_id or record.get("org_id") != org_id or record.get("actor_id") != actor_id:
            raise ValueError("validation_failed")
        with self.transaction(org_id=org_id, actor_id=actor_id) as cur:
            cur.execute(
                "insert into lskills.provider_receipts (org_id,actor_id,kind,receipt_id,request_hash,record) "
                "values (%s,%s,%s,%s,%s,%s) on conflict do nothing",
                (org_id, actor_id, kind, receipt_id, record["request_hash"], Jsonb(dict(record))),
            )
            cur.execute(
                "select request_hash, record from lskills.provider_receipts "
                "where org_id=%s and actor_id=%s and kind=%s and receipt_id=%s",
                (org_id, actor_id, kind, receipt_id),
            )
            stored = cur.fetchone()
            if stored is None or stored["request_hash"] != record["request_hash"]:
                raise ValueError("idempotency_conflict")
            return stored["record"]


class ProductionV2Provider:
    """Share live registry, identity, and receipt behavior between HTTP and MCP."""

    def __init__(self, verifier: Any, store: PostgresProviderStore) -> None:
        self.verifier, self.store = verifier, store
        self._advertisement = V2Provider(lambda token: None)

    def resources(self):
        """Return the core resource contract."""
        return self._advertisement.resources()

    def tools(self):
        """Return the core tool contract."""
        return self._advertisement.tools()

    @property
    def catalog_ready(self) -> bool:
        """Report publication presence without exposing release bodies."""
        try:
            with self.store.transaction() as cur:
                cur.execute("select 1 from lskills.provider_releases where lifecycle='qualified' limit 1")
                return cur.fetchone() is not None
        except Exception:
            return False

    def store_status(self):
        """Return a sanitized production-store readiness result."""
        try:
            return dict(self.store.probe())
        except Exception:
            return {"ready": False, "code": "store_unavailable", "fail_closed": True}

    @staticmethod
    def _page(items: list[dict[str, Any]], request: Mapping[str, Any], snapshot_id: str) -> dict[str, Any]:
        """Apply the v2 bounded pagination shape to metadata-only rows."""
        limit = request.get("limit", 50)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("validation_failed")
        cursor = request.get("cursor")
        offset = 0
        if cursor is not None:
            if not isinstance(cursor, str) or not cursor.startswith(snapshot_id + ":"):
                raise ValueError("validation_failed")
            try:
                offset = int(cursor.rsplit(":", 1)[1])
            except ValueError as exc:
                raise ValueError("validation_failed") from exc
            if offset < 0:
                raise ValueError("validation_failed")
        page = items[offset : offset + limit]
        end = offset + len(page)
        return {"items": page, "has_more": end < len(items),
                "next_cursor": f"{snapshot_id}:{end}" if end < len(items) else None}

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Verify current identity before reading registry state or writing receipts."""
        from .v2_http import identity_from_claims

        operation = str(request.get("operation", ""))
        # Core handles protocol/legacy errors without touching the live database.
        if (operation not in self.tools() + RESOURCE_OPERATIONS
                or request.get("protocol_version") != PROTOCOL_VERSION
                or "session" in request or "session_id" in request):
            return self._advertisement.handle(request)
        token = request.get("authorization")
        if not isinstance(token, str) or not token:
            return {"ok": False, "error": "auth_required"}
        try:
            claims = self.verifier.verify(
                token if token.lower().startswith("bearer ") else f"Bearer {token}",
                request_payload={},
                required_operation="skills_feedback_submit" if operation in WRITE_TOOLS else "skills_list",
            )
            if not claims.org_id or not claims.runtime_binding_id:
                return {"ok": False, "error": "forbidden"}
        except Exception:
            return {"ok": False, "error": "auth_invalid"}
        try:
            # Discovery never needs resource bodies. Keep the binding refresh and
            # RLS checks, but project only bounded release metadata for catalog and
            # release-list operations.
            if hasattr(self.store, "snapshot_metadata") and operation in {
                "skills_catalog_list", "skills_catalog_search", "skills_release_list",
            }:
                releases, binding = self.store.snapshot_metadata(claims)
                filed = filed_releases(releases)
                snapshot_id = "snapshot:" + hashlib.sha256(
                    json.dumps([r["release_id"] for r in releases], separators=(",", ":")).encode()
                ).hexdigest()[:16]
                base = {"ok": True, "kind": "resource", "operation": operation,
                        "contract_version": "skills.api.v0.2", "snapshot_id": snapshot_id,
                        "cursor": f"{snapshot_id}:0", "limit": request.get("limit", 50),
                        "no_fallback": True}
                if operation == "skills_release_list":
                    family_id = request.get("family_id")
                    skill_id = request.get("skill_id")
                    entries = [
                        {k: release.get(k, "") for k in (
                            "skill_id", "version", "release_id", "family_id",
                            "subcategory_id", "collection_id", "lifecycle_state", "qualification"
                        )}
                        for release in filed
                        if (not family_id or release.get("family_id") == family_id)
                        and (not skill_id or release.get("skill_id") == skill_id)
                    ]
                else:
                    # Preserve the explicit live catalog floors and placements;
                    # bound release rows only determine readiness and release list.
                    entries = [
                        {
                            "family_id": family["family_id"],
                            "display_name": family["display_name"],
                            "description": family["description"],
                            "subcategory_count": len(family.get("subcategories", ())),
                        }
                        for family in catalog_families(filed)
                    ]
                    query = str(request.get("query", "")).strip().casefold()
                    if operation == "skills_catalog_search" and query:
                        entries = [entry for entry in entries if query in " ".join(
                            str(entry.get(field, "")) for field in ("family_id", "display_name", "description")
                        ).casefold()]
                base.update(self._page(entries, request, snapshot_id))
                return base

            if hasattr(self.store, "fetch_release") and operation in {
                "skills_release_describe", "skills_qualification_get",
                "skills_release_entrypoint_get", "skills_release_sections_list",
                "skills_release_section_get", "skills_release_resources_list",
                "skills_release_resource_get", "skills_release_content_get",
                "skills_release_package_get", "skills_release_verify",
            }:
                skill_id = request.get("skill_id")
                version = request.get("version")
                release_id = f"{skill_id}@{version}" if isinstance(skill_id, str) and isinstance(version, str) else ""
                if operation in {"skills_release_describe", "skills_qualification_get", "skills_release_resources_list", "skills_release_sections_list"} and hasattr(self.store, "fetch_release_metadata"):
                    metadata = self.store.fetch_release_metadata(claims, release_id)
                    manifest = metadata["row"]["manifest"]
                    binding = metadata["binding"]
                    identity = replace(
                        identity_from_claims(claims),
                        runtime_profiles=frozenset({binding["runtime_profile"]}),
                        activated_release_ids=frozenset(binding["release_ids"]),
                    )
                    governed = _normalize_release({**manifest, "resources": {}})
                    governed = replace(governed, lifecycle_state=str(metadata["row"]["lifecycle"]))
                    self._advertisement._authorize_release(governed, identity, request)
                    snapshot_id = manifest_digest({"release_id": release_id, "manifest_sha256": metadata["row"]["manifest_sha256"]})
                    envelope = {"ok": True, "kind": "resource", "operation": operation, "contract_version": "skills.api.v0.2", "snapshot_id": snapshot_id, "cursor": f"{snapshot_id}:0", "limit": request.get("limit", 50), "no_fallback": True}
                    if operation == "skills_release_describe":
                        self._page([], request, snapshot_id)
                        return {**envelope, "skill_id": manifest.get("skill_id"), "version": manifest.get("version"), "release_id": release_id, "family_id": manifest.get("family_id"), "subcategory_id": manifest.get("subcategory_id"), "lifecycle_state": metadata["row"]["lifecycle"], "qualification": manifest.get("qualification"), "provenance": manifest.get("provenance", {})}
                    if operation == "skills_qualification_get":
                        self._page([], request, snapshot_id)
                        return {**envelope, "skill_id": manifest.get("skill_id"), "version": manifest.get("version"), "release_id": release_id, "qualification": manifest.get("qualification")}
                    descriptors = []
                    for resource_id, descriptor in (manifest.get("resources") or {}).items():
                        if operation == "skills_release_sections_list" and descriptor.get("resource_kind") not in {"section", "entrypoint"}:
                            continue
                        byte_size = descriptor.get("byte_size")
                        if byte_size is None and descriptor.get("content_b64") is not None:
                            byte_size = len(base64.b64decode(descriptor["content_b64"], validate=True))
                        descriptors.append({"schema_version": "0.1", "resource_id": resource_id, "release_id": release_id, "skill_id": manifest.get("skill_id"), "skill_version": manifest.get("version"), "resource_kind": descriptor.get("resource_kind", "entrypoint"), "resource_uri": release_resource_uri(manifest.get("skill_id"), manifest.get("version"), resource_id), "media_type": descriptor.get("media_type", "text/markdown"), "byte_size": byte_size, "content_digest": descriptor.get("content_digest"), "immutable": True, "disclosure_level": descriptor.get("disclosure_level", 3), "provenance": descriptor.get("provenance", manifest.get("provenance", {})), "licence": descriptor.get("licence", descriptor.get("license", {})), "trust_boundary": "linkskills-resource"})
                    return {**envelope, **self._page(descriptors, request, snapshot_id)}
                resource_id = request.get("resource_id") or request.get("content_id")
                if operation == "skills_release_entrypoint_get" and not resource_id:
                    resource_id = "entrypoint"
                if operation == "skills_release_entrypoint_get" and request.get("manifest"):
                    resource_id = "manifest"
                if operation == "skills_release_section_get" and not resource_id:
                    resource_id = request.get("section_id") or request.get("fragment_id")
                selected = {str(resource_id)} if resource_id and operation in {
                    "skills_release_entrypoint_get", "skills_release_section_get",
                    "skills_release_resource_get", "skills_release_content_get",
                } else None
                fetched = self.store.fetch_release(claims, release_id, selected)
                if "decoded_release" in fetched["row"]:
                    release = fetched["row"]["decoded_release"]
                    if selected is not None:
                        release = dict(release)
                        release["resources"] = {
                            key: value for key, value in release["resources"].items() if key in selected
                        }
                        if not release["resources"]:
                            raise ValueError("not_found")
                else:
                    release = decode_release(fetched["row"], selected)
                release = filed_releases([release])[0]
                binding = fetched["binding"]
                identity = replace(identity_from_claims(claims),
                                    runtime_profiles=frozenset({binding["runtime_profile"]}),
                                    activated_release_ids=frozenset(binding["release_ids"]))
                provider = V2Provider(lambda token: identity, releases=[release],
                                      families=catalog_families([release]),
                                      store=self.store, production_store=True,
                                      catalog_version=manifest_digest({"release_id": release_id}))
                return provider.handle(request)

            if operation == "skills_capabilities_get" and hasattr(self.store, "snapshot_metadata"):
                # Capabilities are static protocol metadata. Do not load bound
                # release bodies merely to report the advertised operations, but
                # still refresh the enabled binding and release membership first.
                _releases, binding = self.store.snapshot_metadata(claims)
                identity = replace(identity_from_claims(claims),
                                    runtime_profiles=frozenset({binding["runtime_profile"]}),
                                    activated_release_ids=frozenset(binding["release_ids"]))
                if not identity.org_id or not identity.actor_id or not identity.binding:
                    raise ValueError("auth_invalid")
                if identity.audience != "lskills-api" or "skills.read" not in identity.capabilities:
                    raise ValueError("forbidden")
                self._page([], request, "snapshot:capabilities")
                result = {
                    "ok": True, "kind": "resource", "operation": operation,
                    "contract_version": "skills.api.v0.2", "snapshot_id": "snapshot:capabilities",
                    "cursor": "snapshot:capabilities:0", "limit": request.get("limit", 50),
                    "no_fallback": True, "capabilities": {
                        "resources": True, "tools": True, "pagination": True,
                        "protocol": PROTOCOL_VERSION, "contract_version": "skills.api.v0.2",
                    }, "resources": list(self.resources()), "tools": list(self.tools()),
                    "legacy_execution": False, "catalog_ready": bool(_releases),
                }
                if request.get("domain"):
                    result["domain"] = str(request["domain"])
                    result["guide"] = {"domain": str(request["domain"]),
                                       "disclosure": "bounded_guide_only", "bytes": None}
                return result

            if hasattr(self.store, "snapshot_metadata") and operation in WRITE_TOOLS | {
                "skills_use_report_status_get", "skills_feedback_status_get", "skills_librarian_status_get",
            }:
                # Receipt operations are authorized by the verified actor and do
                # not require a release-body snapshot.
                _releases, binding = self.store.snapshot_metadata(claims)
                identity = replace(identity_from_claims(claims),
                                    runtime_profiles=frozenset({binding["runtime_profile"]}),
                                    activated_release_ids=frozenset(binding["release_ids"]))
                provider = V2Provider(lambda token: identity, releases=[], store=self.store, production_store=True)
                return provider.handle(request)

            releases, binding = self.store.snapshot(claims)
            identity = replace(
                identity_from_claims(claims),
                runtime_profiles=frozenset({binding["runtime_profile"]}),
                activated_release_ids=frozenset(binding["release_ids"]),
            )
            provider = V2Provider(
                lambda token: identity, releases=releases, store=self.store, production_store=True,
                catalog_version=manifest_digest({"releases": [
                    {"id": f"{r['skill_id']}@{r['version']}", "state": r["lifecycle_state"],
                     "resources": {k: v["content_digest"] for k, v in r["resources"].items()}}
                    for r in releases
                ]}),
            )
            return provider.handle(request)
        except ValueError as exc:
            code = str(exc)
            return {"ok": False, "error": code if code in {
                "forbidden", "catalog_unavailable", "integrity_mismatch", "not_qualified",
                "not_found", "validation_failed", "expired_release", "revoked_release"
            } else "catalog_unavailable"}
        except Exception:
            return {"ok": False, "error": "store_unavailable"}


def production_provider(verifier: Any) -> ProductionV2Provider:
    """Require explicit Postgres configuration; never fall back to an empty fixture."""
    from .auth import AuthConfigurationError
    from .postgres_store import resolve_database_url

    dsn = resolve_database_url()
    if os.environ.get("LINKSKILLS_GATEWAY_STORE") != "postgres" or not dsn:
        raise AuthConfigurationError("production v2 requires the Postgres runtime store")
    return ProductionV2Provider(verifier, PostgresProviderStore(dsn))
