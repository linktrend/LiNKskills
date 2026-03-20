from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from supabase import Client, create_client


class MemoryService:
    """Supabase-backed memory store with agent/project isolation."""

    VAULT_MODULE_PATH = Path(__file__).resolve().parents[3] / "vault" / "src" / "vault_logic.py"
    VAULT_DATA_PATH = Path(__file__).resolve().parents[3] / "vault" / "data" / "vault.bin"

    def __init__(self, table_name: str | None = None) -> None:
        self.table_name = table_name or os.getenv("SUPABASE_MEMORY_TABLE", "agent_memory")
        self.supabase_url = self._vault_get(os.getenv("SUPABASE_URL_VAULT_KEY", "SUPABASE_URL"))
        self.supabase_secret = self._vault_get(
            os.getenv("SUPABASE_SECRET_VAULT_KEY", "SUPABASE_SECRET_KEY")
        )
        self.client: Client = create_client(self.supabase_url, self.supabase_secret)

    def remember(self, agent_id: str, project_id: str, content: str) -> dict[str, Any]:
        """Persist one memory row under (agent_id, project_id)."""
        payload = {
            "agent_id": agent_id,
            "project_id": project_id,
            "content": content,
        }
        response = self.client.table(self.table_name).insert(payload).execute()
        rows = self._extract_data(response)
        return {
            "status": "success",
            "table": self.table_name,
            "agent_id": agent_id,
            "project_id": project_id,
            "stored": len(rows),
            "row": rows[0] if rows else payload,
        }

    def recall(self, agent_id: str, project_id: str, query: str, limit: int = 20) -> dict[str, Any]:
        """Recall memories scoped to one agent and project."""
        statement = (
            self.client.table(self.table_name)
            .select("*")
            .eq("agent_id", agent_id)
            .eq("project_id", project_id)
            .limit(limit)
        )
        if query.strip():
            statement = statement.ilike("content", f"%{query.strip()}%")
        response = statement.execute()
        rows = self._extract_data(response)
        return {
            "status": "success",
            "table": self.table_name,
            "agent_id": agent_id,
            "project_id": project_id,
            "query": query,
            "count": len(rows),
            "items": rows,
        }

    def add_note(self, agent_id: str, title: str, md_content: str) -> dict[str, Any]:
        """Store a Markdown note in lsl_memory.notes."""
        normalized_markdown = self._normalize_markdown(md_content)
        payload = {
            "agent_id": agent_id,
            "title": title,
            "md_content": normalized_markdown,
        }
        response = self._notes_table().insert(payload).execute()
        rows = self._extract_data(response)
        return {
            "status": "success",
            "table": "lsl_memory.notes",
            "agent_id": agent_id,
            "stored": len(rows),
            "row": rows[0] if rows else payload,
        }

    def get_note(
        self,
        agent_id: str,
        note_id: str | None = None,
        title: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Retrieve Markdown notes from lsl_memory.notes."""
        query = (
            self._notes_table()
            .select("id,agent_id,title,md_content,created_at")
            .eq("agent_id", agent_id)
            .limit(max(1, limit))
            .order("created_at", desc=True)
        )
        if note_id:
            query = query.eq("id", note_id).limit(1)
        if title:
            query = query.ilike("title", f"%{title.strip()}%")

        response = query.execute()
        rows = self._extract_data(response)
        return {
            "status": "success",
            "table": "lsl_memory.notes",
            "agent_id": agent_id,
            "count": len(rows),
            "items": rows,
        }

    def _extract_data(self, response: Any) -> list[dict[str, Any]]:
        data = getattr(response, "data", None)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return [data]
        return []

    def _normalize_markdown(self, content: str) -> str:
        if not isinstance(content, str):
            raise ValueError("md_content must be a string")
        normalized = content.replace("\r\n", "\n").strip()
        if not normalized:
            raise ValueError("md_content must be non-empty Markdown")
        # Plain text is valid Markdown; preserve input while enforcing text storage.
        return normalized

    def _notes_table(self) -> Any:
        schema_fn = getattr(self.client, "schema", None)
        if callable(schema_fn):
            return self.client.schema("lsl_memory").table("notes")
        return self.client.table("lsl_memory.notes")

    def _vault_get(self, key_name: str) -> str:
        master_key = os.getenv("LSL_MASTER_KEY", "").strip()
        if not master_key:
            raise RuntimeError("LSL_MASTER_KEY is required for memory vault lookup.")
        if not self.VAULT_MODULE_PATH.exists():
            raise RuntimeError(f"Vault module not found: {self.VAULT_MODULE_PATH}")

        spec = importlib.util.spec_from_file_location("lsl_vault_logic", str(self.VAULT_MODULE_PATH))
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load vault module for Supabase credentials.")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        vault_store_cls = getattr(module, "VaultStore", None)
        if vault_store_cls is None:
            raise RuntimeError("VaultStore class not found in vault module.")

        vault = vault_store_cls(data_path=self.VAULT_DATA_PATH, master_key=master_key)
        try:
            value = str(vault.get_value(key_name)).strip()
        except KeyError as exc:
            raise RuntimeError(
                f"Missing vault secret '{key_name}'. Run: ltr vault set {key_name} <value>"
            ) from exc
        if not value:
            raise RuntimeError(
                f"Vault secret '{key_name}' is empty. Run: ltr vault set {key_name} <value>"
            )
        return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LiNKskills Supabase memory CLI")
    parser.add_argument("--version", action="version", version="memory 1.1.0")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    remember_parser = subparsers.add_parser("remember", help="Store one memory item")
    remember_parser.add_argument("--agent-id", required=True, type=str)
    remember_parser.add_argument("--project-id", required=True, type=str)
    remember_parser.add_argument("--content", required=True, type=str)

    recall_parser = subparsers.add_parser("recall", help="Recall memory items")
    recall_parser.add_argument("--agent-id", required=True, type=str)
    recall_parser.add_argument("--project-id", required=True, type=str)
    recall_parser.add_argument("--query", default="", type=str)
    recall_parser.add_argument("--limit", default=20, type=int)

    add_note_parser = subparsers.add_parser("add-note", help="Store one Markdown note")
    add_note_parser.add_argument("--agent-id", required=True, type=str)
    add_note_parser.add_argument("--title", required=True, type=str)
    add_note_parser.add_argument("--md-content", default=None, type=str)
    add_note_parser.add_argument("--md-file", default=None, type=str)

    get_note_parser = subparsers.add_parser("get-note", help="Retrieve Markdown notes")
    get_note_parser.add_argument("--agent-id", required=True, type=str)
    get_note_parser.add_argument("--note-id", default=None, type=str)
    get_note_parser.add_argument("--title", default=None, type=str)
    get_note_parser.add_argument("--limit", default=20, type=int)

    return parser


def _resolve_markdown_content(md_content: str | None, md_file: str | None) -> str:
    if md_content and md_content.strip():
        return md_content
    if md_file:
        path = Path(md_file).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Markdown file not found: {path}")
        return path.read_text(encoding="utf-8")
    raise ValueError("Provide --md-content or --md-file")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        service = MemoryService()
        if args.command == "remember":
            result = service.remember(
                agent_id=args.agent_id,
                project_id=args.project_id,
                content=args.content,
            )
        elif args.command == "recall":
            result = service.recall(
                agent_id=args.agent_id,
                project_id=args.project_id,
                query=args.query,
                limit=max(1, int(args.limit)),
            )
        elif args.command == "add-note":
            md_content = _resolve_markdown_content(args.md_content, args.md_file)
            result = service.add_note(
                agent_id=args.agent_id,
                title=args.title,
                md_content=md_content,
            )
        elif args.command == "get-note":
            result = service.get_note(
                agent_id=args.agent_id,
                note_id=args.note_id,
                title=args.title,
                limit=max(1, int(args.limit)),
            )
        else:
            raise ValueError(f"Unsupported command: {args.command}")

        print(
            json.dumps(
                {"status": "success", "output": result, "path": service.table_name},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "output": str(exc), "path": "supabase"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
