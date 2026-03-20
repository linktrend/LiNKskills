from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

import click

from services.calendar import CalendarService
from services.chat import ChatService
from services.docs import DocsService
from services.drive import DriveService
from services.gmail import GmailService
from services.analytics import AnalyticsService
from services.ads import AdsService
from services.env_context import EnvContextService
from services.forms import FormsService
from services.maps_routes import MapsRoutesService
from services.news import NewsService
from services.search_console import SearchConsoleService
from services.sheets import SheetsService
from services.slides import SlidesService
from services.tasks import TasksService
from services.yt_analytics import YTAnalyticsService
from services.youtube import YouTubeService
from utils.auth import LTRAuth
from utils.logging import LTRAuditLogger

VERSION = "v2.1.0"
ACTIVE_SERVICES = [
    "analytics",
    "yt_analytics",
    "search_console",
    "ads",
    "news",
    "maps_routes",
    "env_context",
    "youtube",
    "vault",
    "sandbox",
]

SCOPE_REFRESH_HINT = "Please delete tools/ltr/src/token.json and run 'ltr setup' to refresh scopes."
LOCAL_TOKEN_PATH = Path(__file__).resolve().parent / "token.json"
REPO_ROOT = Path(__file__).resolve().parents[3]
VAULT_MODULE_PATH = REPO_ROOT / "tools" / "vault" / "src" / "vault_logic.py"
SANDBOX_MODULE_PATH = REPO_ROOT / "tools" / "sandbox" / "src" / "docker_runtime.py"
VAULT_DATA_PATH = REPO_ROOT / "tools" / "vault" / "data" / "vault.bin"
USAGE_MODULE_PATH = REPO_ROOT / "tools" / "usage" / "src" / "usage_logic.py"
SECURE_ENV_MESSAGE = (
    "Secure Environment Required: set LSL_MASTER_KEY before running ltr commands."
)
COMMAND_START_TS = time.perf_counter()


def _log_usage_event(payload: dict[str, Any], exit_code: int) -> None:
    try:
        if not USAGE_MODULE_PATH.exists():
            return
        module = _load_external_module("lsl_usage_logic", USAGE_MODULE_PATH)
        tracker_cls = getattr(module, "LangfuseUsageTracker", None)
        if tracker_cls is None:
            return

        tracker = tracker_cls(repo_root=REPO_ROOT)
        success = bool(payload.get("ok", exit_code == 0))
        latency_ms = int((time.perf_counter() - COMMAND_START_TS) * 1000)
        tracker.log_execution(
            service=str(payload.get("service", "core")),
            action=str(payload.get("action", "unknown")),
            success=success,
            latency_ms=latency_ms,
            metadata={
                "exit_code": exit_code,
                "error": payload.get("error"),
            },
        )
    except Exception as exc:
        logger = LTRAuditLogger()
        logger.log_event(
            service="usage",
            action="usage.log",
            status="error",
            resource_id=str(exc)[:160],
        )


def emit(payload: dict[str, Any], exit_code: int = 0) -> None:
    """Write deterministic JSON output and terminate."""
    _log_usage_event(payload=payload, exit_code=exit_code)
    click.echo(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    raise SystemExit(exit_code)


def _error_message_with_scope_hint(result: dict[str, Any], default_message: str) -> str:
    message = str(result.get("message", default_message))
    message_lower = message.lower()
    code = str(result.get("code", "")).lower()
    is_scope_or_403 = (
        "403" in message
        or "insufficient authentication scopes" in message_lower
        or "permission_denied" in message_lower
        or code.endswith("forbidden")
    )
    if is_scope_or_403 and SCOPE_REFRESH_HINT not in message:
        return f"{message} {SCOPE_REFRESH_HINT}"
    return message


def _load_sandbox_runtime_class() -> Any:
    module = _load_external_module("lsl_sandbox_runtime", SANDBOX_MODULE_PATH)
    runtime_cls = getattr(module, "DockerRuntime", None)
    if runtime_cls is None:
        raise AttributeError("DockerRuntime class not found in docker_runtime.py")
    return runtime_cls


def _require_secure_environment() -> None:
    if os.getenv("LSL_MASTER_KEY", "").strip():
        return

    logger = LTRAuditLogger()
    logger.log_event(
        service="core",
        action="security.master_key.check",
        status="error",
        resource_id="LSL_MASTER_KEY",
    )
    click.echo(
        json.dumps(
            {
                "ok": False,
                "service": "core",
                "action": "security.master_key.check",
                "data": {},
                "error": {
                    "code": "SECURE_ENV_REQUIRED",
                    "message": SECURE_ENV_MESSAGE,
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    raise SystemExit(1)


class ExecutionService:
    """Command execution router with sandbox-by-default enforcement."""

    def __init__(self, use_sandbox: bool = True, allow_network: bool = False) -> None:
        self.use_sandbox = use_sandbox
        self.allow_network = allow_network
        self.logger = LTRAuditLogger()

    def run(self, command: str) -> dict[str, Any]:
        if self.use_sandbox:
            return self._run_in_sandbox(command)
        return self._run_local(command)

    def _run_in_sandbox(self, command: str) -> dict[str, Any]:
        def audit_callback(event_action: str, status: str, resource_id: str) -> None:
            self.logger.log_event(
                service="sandbox",
                action=event_action,
                status=status,
                resource_id=resource_id,
            )

        runtime_cls = _load_sandbox_runtime_class()
        runtime = runtime_cls(
            image="python:3.11-slim",
            mem_limit="512m",
            network_disabled=not self.allow_network,
            audit_callback=audit_callback,
        )
        return runtime.run(command=command, cwd=Path.cwd())

    def _run_local(self, command: str) -> dict[str, Any]:
        self.logger.log_event(
            service="sandbox",
            action="sandbox.bypass.local_exec",
            status="start",
            resource_id=command,
        )
        completed = subprocess.run(
            ["/bin/sh", "-lc", command],
            capture_output=True,
            text=True,
            check=False,
        )
        status = "success" if completed.returncode == 0 else "error"
        self.logger.log_event(
            service="sandbox",
            action="sandbox.bypass.local_exec",
            status=status,
            resource_id=command,
        )
        return {
            "status": status,
            "command": command,
            "image": "host",
            "network_disabled": False,
            "cwd": str(Path.cwd()),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "exit_code": completed.returncode,
        }


def _version_callback(ctx: click.Context, _param: click.Option, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    _require_secure_environment()
    emit(
        {
            "ok": True,
            "service": "core",
            "action": "ltr.version",
            "data": {
                "version": VERSION,
                "services": ACTIVE_SERVICES,
            },
            "error": None,
        }
    )


@click.group(name="ltr", invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_version_callback,
)
@click.option(
    "--no-sandbox",
    is_flag=True,
    default=False,
    help="Bypass default container sandbox for command execution (human override only).",
)
@click.pass_context
def ltr(ctx: click.Context, no_sandbox: bool) -> None:
    """Gateway root group."""
    _require_secure_environment()
    ctx.ensure_object(dict)
    ctx.obj["use_sandbox"] = not no_sandbox
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "core",
                "action": "ltr.root",
                "data": {
                    "group": "ltr",
                    "use_sandbox": bool(ctx.obj["use_sandbox"]),
                },
                "error": None,
            }
        )


def _emit_service_moved_to_gws(service_name: str) -> None:
    emit(
        {
            "ok": False,
            "service": service_name,
            "action": f"{service_name}.moved",
            "data": {},
            "error": {
                "code": "SERVICE_MOVED_TO_GWS",
                "message": (
                    f"Service '{service_name}' is now provided by gws. "
                    f"Use: gws {service_name} ..."
                ),
            },
        },
        exit_code=1,
    )


@ltr.group(name="gmail", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def gmail(ctx: click.Context, config_path: Path) -> None:
    """Gmail service group scaffold."""
    ctx.obj["gmail_config_path"] = config_path
    _emit_service_moved_to_gws("gmail")


@ltr.group(name="drive", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def drive(ctx: click.Context, config_path: Path) -> None:
    """Drive service group scaffold."""
    ctx.obj["drive_config_path"] = config_path
    _emit_service_moved_to_gws("drive")


@ltr.group(name="docs", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def docs(ctx: click.Context, config_path: Path) -> None:
    """Docs service group scaffold."""
    ctx.obj["docs_config_path"] = config_path
    _emit_service_moved_to_gws("docs")


@ltr.group(name="sheets", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def sheets(ctx: click.Context, config_path: Path) -> None:
    """Sheets service group scaffold."""
    ctx.obj["sheets_config_path"] = config_path
    _emit_service_moved_to_gws("sheets")


@ltr.group(name="calendar", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def calendar(ctx: click.Context, config_path: Path) -> None:
    """Calendar service group scaffold."""
    ctx.obj["calendar_config_path"] = config_path
    _emit_service_moved_to_gws("calendar")


@ltr.group(name="analytics", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def analytics(ctx: click.Context, config_path: Path) -> None:
    """Analytics service group scaffold."""
    ctx.obj["analytics_config_path"] = config_path
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "analytics",
                "action": "analytics.root",
                "data": {"group": "analytics"},
                "error": None,
            }
        )


@ltr.group(name="search-console", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def search_console(ctx: click.Context, config_path: Path) -> None:
    """Search Console service group scaffold."""
    ctx.obj["search_console_config_path"] = config_path
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "search-console",
                "action": "search_console.root",
                "data": {"group": "search-console"},
                "error": None,
            }
        )


@ltr.group(name="forms", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def forms(ctx: click.Context, config_path: Path) -> None:
    """Forms service group scaffold."""
    ctx.obj["forms_config_path"] = config_path
    _emit_service_moved_to_gws("forms")


@ltr.group(name="ads", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def ads(ctx: click.Context, config_path: Path) -> None:
    """Ads service group scaffold."""
    ctx.obj["ads_config_path"] = config_path
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "ads",
                "action": "ads.root",
                "data": {"group": "ads"},
                "error": None,
            }
        )


@ltr.group(name="news", invoke_without_command=True)
@click.pass_context
def news(ctx: click.Context) -> None:
    """News service group scaffold."""
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "news",
                "action": "news.root",
                "data": {"group": "news"},
                "error": None,
            }
        )


@ltr.group(name="maps", invoke_without_command=True)
@click.pass_context
def maps(ctx: click.Context) -> None:
    """Maps/Routes service group scaffold."""
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "maps",
                "action": "maps.root",
                "data": {"group": "maps"},
                "error": None,
            }
        )


@ltr.group(name="env", invoke_without_command=True)
@click.pass_context
def env(ctx: click.Context) -> None:
    """Environment context service group scaffold."""
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "env",
                "action": "env.root",
                "data": {"group": "env"},
                "error": None,
            }
        )


@ltr.group(name="slides", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def slides(ctx: click.Context, config_path: Path) -> None:
    """Slides service group scaffold."""
    ctx.obj["slides_config_path"] = config_path
    _emit_service_moved_to_gws("slides")


@ltr.group(name="tasks", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def tasks(ctx: click.Context, config_path: Path) -> None:
    """Tasks service group scaffold."""
    ctx.obj["tasks_config_path"] = config_path
    _emit_service_moved_to_gws("tasks")


@ltr.group(name="youtube", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def youtube(ctx: click.Context, config_path: Path) -> None:
    """YouTube service group scaffold."""
    ctx.obj["youtube_config_path"] = config_path
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "youtube",
                "action": "youtube.root",
                "data": {"group": "youtube"},
                "error": None,
            }
        )


@ltr.group(name="chat", invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("credentials.json"),
    show_default=True,
)
@click.pass_context
def chat(ctx: click.Context, config_path: Path) -> None:
    """Chat service group scaffold."""
    ctx.obj["chat_config_path"] = config_path
    _emit_service_moved_to_gws("chat")


@ltr.group(name="vault", invoke_without_command=True)
@click.pass_context
def vault(ctx: click.Context) -> None:
    """Secure vault service group scaffold."""
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "vault",
                "action": "vault.root",
                "data": {"group": "vault"},
                "error": None,
            }
        )


@ltr.group(name="sandbox", invoke_without_command=True)
@click.pass_context
def sandbox(ctx: click.Context) -> None:
    """Sandbox runtime service group scaffold."""
    if ctx.invoked_subcommand is None:
        emit(
            {
                "ok": True,
                "service": "sandbox",
                "action": "sandbox.root",
                "data": {"group": "sandbox"},
                "error": None,
            }
        )


def _emit_gmail_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("message_id")
        or result.get("thread_id")
        or result.get("resource_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="gmail",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "gmail",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "gmail",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GMAIL_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown Gmail error"),
            },
        },
        exit_code=1,
    )


def _run_gmail_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[GmailService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("gmail_config_path", "credentials.json"))
        service = GmailService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GMAIL_INIT_FAILED",
            "message": str(exc),
        }

    _emit_gmail_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _emit_drive_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("resource_id")
        or result.get("file_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="drive",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "drive",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "drive",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GDRIVE_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown Drive error"),
            },
        },
        exit_code=1,
    )


def _run_drive_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[DriveService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("drive_config_path", "credentials.json"))
        service = DriveService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GDRIVE_INIT_FAILED",
            "message": str(exc),
        }

    _emit_drive_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _emit_docs_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("document_id")
        or result.get("resource_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="docs",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "docs",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "docs",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GDOCS_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown Docs error"),
            },
        },
        exit_code=1,
    )


def _run_docs_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[DocsService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("docs_config_path", "credentials.json"))
        service = DocsService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GDOCS_INIT_FAILED",
            "message": str(exc),
        }

    _emit_docs_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _emit_sheets_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("spreadsheet_id")
        or result.get("resource_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="sheets",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "sheets",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "sheets",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GSHEETS_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown Sheets error"),
            },
        },
        exit_code=1,
    )


def _run_sheets_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[SheetsService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("sheets_config_path", "credentials.json"))
        service = SheetsService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GSHEETS_INIT_FAILED",
            "message": str(exc),
        }

    _emit_sheets_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _emit_calendar_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("event_id")
        or result.get("resource_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="calendar",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "calendar",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "calendar",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GCALENDAR_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown Calendar error"),
            },
        },
        exit_code=1,
    )


def _run_calendar_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[CalendarService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("calendar_config_path", "credentials.json"))
        service = CalendarService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GCALENDAR_INIT_FAILED",
            "message": str(exc),
        }

    _emit_calendar_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _emit_slides_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("object_id")
        or result.get("presentation_id")
        or result.get("resource_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="slides",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "slides",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "slides",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GSLIDES_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown Slides error"),
            },
        },
        exit_code=1,
    )


def _run_slides_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[SlidesService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("slides_config_path", "credentials.json"))
        service = SlidesService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GSLIDES_INIT_FAILED",
            "message": str(exc),
        }

    _emit_slides_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _emit_tasks_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("task_id")
        or result.get("list_id")
        or result.get("resource_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="tasks",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "tasks",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "tasks",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GTASKS_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown Tasks error"),
            },
        },
        exit_code=1,
    )


def _run_tasks_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[TasksService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("tasks_config_path", "credentials.json"))
        service = TasksService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GTASKS_INIT_FAILED",
            "message": str(exc),
        }

    _emit_tasks_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _emit_youtube_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("video_id")
        or result.get("comment_id")
        or result.get("channel_id")
        or result.get("resource_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="youtube",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "youtube",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "youtube",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GYOUTUBE_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown YouTube error"),
            },
        },
        exit_code=1,
    )


def _run_youtube_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[YouTubeService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("youtube_config_path", "credentials.json"))
        service = YouTubeService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GYOUTUBE_INIT_FAILED",
            "message": str(exc),
        }

    _emit_youtube_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _emit_service_result(
    service_name: str,
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
    default_code: str,
    default_message: str,
    resource_keys: list[str],
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id: str = resource_id_fallback
    for key in resource_keys:
        value = result.get(key)
        if value:
            resource_id = str(value)
            break

    logger.log_event(
        service=service_name,
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": service_name,
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": service_name,
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", default_code)),
                "message": _error_message_with_scope_hint(result, default_message),
            },
        },
        exit_code=1,
    )


def _run_analytics_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[AnalyticsService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("analytics_config_path", "credentials.json"))
        service = AnalyticsService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {"status": "error", "code": "GANALYTICS_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="analytics",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="GANALYTICS_UNKNOWN_ERROR",
        default_message="Unknown Analytics error",
        resource_keys=["property_id", "resource_id"],
    )


def _run_yt_analytics_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[YTAnalyticsService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("analytics_config_path", "credentials.json"))
        service = YTAnalyticsService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {"status": "error", "code": "GYT_ANALYTICS_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="yt_analytics",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="GYT_ANALYTICS_UNKNOWN_ERROR",
        default_message="Unknown YouTube Analytics error",
        resource_keys=["job_id", "resource_id"],
    )


def _run_search_console_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[SearchConsoleService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("search_console_config_path", "credentials.json"))
        service = SearchConsoleService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {"status": "error", "code": "GSC_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="search-console",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="GSC_UNKNOWN_ERROR",
        default_message="Unknown Search Console error",
        resource_keys=["site_url", "resource_id"],
    )


def _run_forms_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[FormsService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("forms_config_path", "credentials.json"))
        service = FormsService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {"status": "error", "code": "GFORMS_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="forms",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="GFORMS_UNKNOWN_ERROR",
        default_message="Unknown Forms error",
        resource_keys=["form_id", "response_id", "resource_id"],
    )


def _run_ads_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[AdsService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("ads_config_path", "credentials.json"))
        service = AdsService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {"status": "error", "code": "GADS_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="ads",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="GADS_UNKNOWN_ERROR",
        default_message="Unknown Ads error",
        resource_keys=["customer_id", "campaign_id", "resource_id"],
    )


def _run_news_action(
    action: str,
    resource_id_fallback: str,
    executor: Callable[[NewsService], dict[str, Any]],
) -> None:
    try:
        service = NewsService()
        result = executor(service)
    except Exception as exc:
        result = {"status": "error", "code": "GNEWS_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="news",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="GNEWS_UNKNOWN_ERROR",
        default_message="Unknown News error",
        resource_keys=["query", "resource_id"],
    )


def _run_maps_action(
    action: str,
    resource_id_fallback: str,
    executor: Callable[[MapsRoutesService], dict[str, Any]],
) -> None:
    try:
        service = MapsRoutesService()
        result = executor(service)
    except Exception as exc:
        result = {"status": "error", "code": "GMAPS_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="maps",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="GMAPS_UNKNOWN_ERROR",
        default_message="Unknown Maps error",
        resource_keys=["place_id", "origin", "resource_id"],
    )


def _run_env_action(
    action: str,
    resource_id_fallback: str,
    executor: Callable[[EnvContextService], dict[str, Any]],
) -> None:
    try:
        service = EnvContextService()
        result = executor(service)
    except Exception as exc:
        result = {"status": "error", "code": "GENV_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="env",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="GENV_UNKNOWN_ERROR",
        default_message="Unknown Env Context error",
        resource_keys=["timezone", "resource_id"],
    )


def _load_external_module(module_name: str, module_path: Path) -> Any:
    if not module_path.exists():
        raise FileNotFoundError(f"Module not found: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_vault_action(
    action: str,
    resource_id_fallback: str,
    executor: Callable[[Any], dict[str, Any]],
) -> None:
    logger = LTRAuditLogger()

    def audit_callback(event_action: str, status: str, resource_id: str) -> None:
        logger.log_event(
            service="vault",
            action=event_action,
            status=status,
            resource_id=resource_id,
        )

    try:
        module = _load_external_module("lsl_vault_logic", VAULT_MODULE_PATH)
        vault_store_cls = getattr(module, "VaultStore", None)
        if vault_store_cls is None:
            raise AttributeError("VaultStore class not found in vault_logic.py")

        vault_store = vault_store_cls(
            data_path=VAULT_DATA_PATH,
            audit_callback=audit_callback,
        )
        result = executor(vault_store)
    except Exception as exc:
        result = {"status": "error", "code": "VAULT_INIT_FAILED", "message": str(exc)}

    _emit_service_result(
        service_name="vault",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="VAULT_UNKNOWN_ERROR",
        default_message="Unknown Vault error",
        resource_keys=["key", "resource_id"],
    )


def _run_sandbox_action(
    action: str,
    resource_id_fallback: str,
    command: str,
    use_sandbox: bool,
    allow_network: bool,
) -> None:
    try:
        execution_service = ExecutionService(
            use_sandbox=use_sandbox,
            allow_network=allow_network,
        )
        result = execution_service.run(command=command)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "SANDBOX_INIT_FAILED",
            "message": str(exc),
            "command": command,
        }

    _emit_service_result(
        service_name="sandbox",
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
        default_code="SANDBOX_UNKNOWN_ERROR",
        default_message="Unknown Sandbox error",
        resource_keys=["command", "resource_id"],
    )


def _emit_chat_result(
    action: str,
    result: dict[str, Any],
    resource_id_fallback: str,
) -> None:
    logger = LTRAuditLogger()
    status = str(result.get("status", "error"))
    resource_id = str(
        result.get("message_name")
        or result.get("space_name")
        or result.get("membership_name")
        or result.get("resource_id")
        or resource_id_fallback
    )
    logger.log_event(
        service="chat",
        action=action,
        status=status,
        resource_id=resource_id,
    )

    if status == "success":
        emit(
            {
                "ok": True,
                "service": "chat",
                "action": action,
                "data": result,
                "error": None,
            }
        )

    emit(
        {
            "ok": False,
            "service": "chat",
            "action": action,
            "data": {},
            "error": {
                "code": str(result.get("code", "GCHAT_UNKNOWN_ERROR")),
                "message": _error_message_with_scope_hint(result, "Unknown Chat error"),
            },
        },
        exit_code=1,
    )


def _run_chat_action(
    ctx: click.Context,
    action: str,
    resource_id_fallback: str,
    executor: Callable[[ChatService], dict[str, Any]],
) -> None:
    try:
        config_path = Path(ctx.obj.get("chat_config_path", "credentials.json"))
        service = ChatService(config_path=config_path)
        result = executor(service)
    except Exception as exc:
        result = {
            "status": "error",
            "code": "GCHAT_INIT_FAILED",
            "message": str(exc),
        }

    _emit_chat_result(
        action=action,
        result=result,
        resource_id_fallback=resource_id_fallback,
    )


def _parse_values(values_json: str) -> list[Any] | list[list[Any]]:
    parsed: Any = json.loads(values_json)
    if not isinstance(parsed, list):
        raise ValueError("values must be a JSON array")
    if not parsed:
        return parsed
    nested_flags = [isinstance(item, list) for item in parsed]
    if any(nested_flags) and not all(nested_flags):
        raise ValueError("values must be a flat list or a list of lists")
    if all(nested_flags):
        return parsed
    return parsed


def _parse_string_list(raw_json: str) -> list[str]:
    parsed: Any = json.loads(raw_json)
    if not isinstance(parsed, list):
        raise ValueError("value must be a JSON array of strings")
    if not all(isinstance(item, str) for item in parsed):
        raise ValueError("all array items must be strings")
    return parsed


def _parse_coordinate(raw_json: str) -> dict[str, float]:
    parsed: Any = json.loads(raw_json)
    if not isinstance(parsed, dict):
        raise ValueError("coordinate must be a JSON object with lat/lng")
    lat = parsed.get("lat")
    lng = parsed.get("lng")
    if lat is None or lng is None:
        raise ValueError("coordinate requires 'lat' and 'lng'")
    return {"lat": float(lat), "lng": float(lng)}


def _parse_coordinate_list(raw_json: str) -> list[dict[str, float]]:
    parsed: Any = json.loads(raw_json)
    if not isinstance(parsed, list):
        raise ValueError("stops must be a JSON array of coordinates")
    normalized: list[dict[str, float]] = []
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("each stop must be a JSON object with lat/lng")
        lat = item.get("lat")
        lng = item.get("lng")
        if lat is None or lng is None:
            raise ValueError("each stop requires 'lat' and 'lng'")
        normalized.append({"lat": float(lat), "lng": float(lng)})
    return normalized


@gmail.command(name="send")
@click.option("--to", "to_email", required=True, type=str)
@click.option("--subject", required=True, type=str)
@click.option("--body", required=True, type=str)
@click.option("--cc", default=None, type=str)
@click.option("--bcc", default=None, type=str)
@click.option(
    "--attachment",
    "attachments",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.pass_context
def gmail_send(
    ctx: click.Context,
    to_email: str,
    subject: str,
    body: str,
    cc: str | None,
    bcc: str | None,
    attachments: tuple[Path, ...],
) -> None:
    """Send an email."""

    def executor(service: GmailService) -> dict[str, Any]:
        attachment_paths = [str(path) for path in attachments] if attachments else None
        return service.send(
            to=to_email,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            attachments=attachment_paths,
        )

    _run_gmail_action(
        ctx=ctx,
        action="gmail.send",
        resource_id_fallback=to_email,
        executor=executor,
    )


@gmail.command(name="list")
@click.option("--label", default="INBOX", show_default=True, type=str)
@click.option("--max-results", default=10, show_default=True, type=click.IntRange(1, 100))
@click.pass_context
def gmail_list(ctx: click.Context, label: str, max_results: int) -> None:
    """List messages by label."""

    def executor(service: GmailService) -> dict[str, Any]:
        return service.list_messages(label=label, max_results=max_results)

    _run_gmail_action(
        ctx=ctx,
        action="gmail.list",
        resource_id_fallback=label,
        executor=executor,
    )


@gmail.command(name="get")
@click.argument("message_id", type=str)
@click.pass_context
def gmail_get(ctx: click.Context, message_id: str) -> None:
    """Get a single message by id."""

    def executor(service: GmailService) -> dict[str, Any]:
        return service.get_message(message_id=message_id)

    _run_gmail_action(
        ctx=ctx,
        action="gmail.get",
        resource_id_fallback=message_id,
        executor=executor,
    )


@gmail.command(name="search")
@click.option("--query", required=True, type=str)
@click.pass_context
def gmail_search(ctx: click.Context, query: str) -> None:
    """Search Gmail threads."""

    def executor(service: GmailService) -> dict[str, Any]:
        return service.search(query=query)

    _run_gmail_action(
        ctx=ctx,
        action="gmail.search",
        resource_id_fallback=query,
        executor=executor,
    )


@drive.command(name="list")
@click.option("--query", default=None, type=str)
@click.option("--limit", default=10, show_default=True, type=click.IntRange(1, 100))
@click.pass_context
def drive_list(ctx: click.Context, query: str | None, limit: int) -> None:
    """List Drive files."""

    def executor(service: DriveService) -> dict[str, Any]:
        return service.list_files(query=query, page_size=limit)

    _run_drive_action(
        ctx=ctx,
        action="drive.list",
        resource_id_fallback=query or "all",
        executor=executor,
    )


@drive.command(name="upload")
@click.option(
    "--file-path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--folder-id", default=None, type=str)
@click.option("--convert/--no-convert", default=False, show_default=True)
@click.pass_context
def drive_upload(
    ctx: click.Context,
    file_path: Path,
    folder_id: str | None,
    convert: bool,
) -> None:
    """Upload a local file to Drive."""

    def executor(service: DriveService) -> dict[str, Any]:
        return service.upload(
            file_path=str(file_path),
            folder_id=folder_id,
            convert=convert,
        )

    _run_drive_action(
        ctx=ctx,
        action="drive.upload",
        resource_id_fallback=str(file_path),
        executor=executor,
    )


@drive.command(name="download")
@click.option("--file-id", required=True, type=str)
@click.option(
    "--local-path",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
)
@click.pass_context
def drive_download(ctx: click.Context, file_id: str, local_path: Path) -> None:
    """Download a Drive file to local storage."""

    def executor(service: DriveService) -> dict[str, Any]:
        return service.download(file_id=file_id, local_path=str(local_path))

    _run_drive_action(
        ctx=ctx,
        action="drive.download",
        resource_id_fallback=file_id,
        executor=executor,
    )


@drive.command(name="mkdir")
@click.option("--name", required=True, type=str)
@click.option("--parent-id", default=None, type=str)
@click.pass_context
def drive_mkdir(ctx: click.Context, name: str, parent_id: str | None) -> None:
    """Create a Drive folder."""

    def executor(service: DriveService) -> dict[str, Any]:
        return service.create_folder(name=name, parent_id=parent_id)

    _run_drive_action(
        ctx=ctx,
        action="drive.mkdir",
        resource_id_fallback=name,
        executor=executor,
    )


@drive.command(name="share")
@click.option("--file-id", required=True, type=str)
@click.option(
    "--role",
    default="reader",
    show_default=True,
    type=click.Choice(["reader", "commenter", "writer"], case_sensitive=False),
)
@click.option("--notify/--no-notify", default=True, show_default=True)
@click.option(
    "--recipient",
    default=DriveService.ALLOWED_SHARE_RECIPIENT,
    show_default=True,
    type=str,
)
@click.pass_context
def drive_share(
    ctx: click.Context,
    file_id: str,
    role: str,
    notify: bool,
    recipient: str,
) -> None:
    """Share a Drive file with strict recipient controls."""

    def executor(service: DriveService) -> dict[str, Any]:
        return service.share(
            file_id=file_id,
            role=role.lower(),
            notify=notify,
            recipient=recipient,
        )

    _run_drive_action(
        ctx=ctx,
        action="drive.share",
        resource_id_fallback=f"{file_id}:{recipient}",
        executor=executor,
    )


@docs.command(name="create")
@click.option("--title", required=True, type=str)
@click.pass_context
def docs_create(ctx: click.Context, title: str) -> None:
    """Create a blank document."""

    def executor(service: DocsService) -> dict[str, Any]:
        return service.create(title=title)

    _run_docs_action(
        ctx=ctx,
        action="docs.create",
        resource_id_fallback=title,
        executor=executor,
    )


@docs.command(name="read")
@click.option("--document-id", required=True, type=str)
@click.pass_context
def docs_read(ctx: click.Context, document_id: str) -> None:
    """Read plain-text content from a document."""

    def executor(service: DocsService) -> dict[str, Any]:
        return service.get_content(document_id=document_id)

    _run_docs_action(
        ctx=ctx,
        action="docs.read",
        resource_id_fallback=document_id,
        executor=executor,
    )


@docs.command(name="append")
@click.option("--document-id", required=True, type=str)
@click.option("--text", required=True, type=str)
@click.option("--markdown/--no-markdown", default=False, show_default=True)
@click.pass_context
def docs_append(
    ctx: click.Context,
    document_id: str,
    text: str,
    markdown: bool,
) -> None:
    """Append text to the end of a document."""

    def executor(service: DocsService) -> dict[str, Any]:
        if markdown:
            return service.append_markdown(document_id=document_id, markdown_text=text)
        return service.append_text(document_id=document_id, text=text)

    _run_docs_action(
        ctx=ctx,
        action="docs.append",
        resource_id_fallback=document_id,
        executor=executor,
    )


@docs.command(name="replace")
@click.option("--document-id", required=True, type=str)
@click.option("--placeholder", required=True, type=str)
@click.option("--replacement", required=True, type=str)
@click.pass_context
def docs_replace(
    ctx: click.Context,
    document_id: str,
    placeholder: str,
    replacement: str,
) -> None:
    """Replace all placeholder occurrences with replacement text."""

    def executor(service: DocsService) -> dict[str, Any]:
        return service.replace_text(
            document_id=document_id,
            placeholder=placeholder,
            replacement=replacement,
        )

    _run_docs_action(
        ctx=ctx,
        action="docs.replace",
        resource_id_fallback=document_id,
        executor=executor,
    )


@sheets.command(name="create")
@click.option("--title", required=True, type=str)
@click.pass_context
def sheets_create(ctx: click.Context, title: str) -> None:
    """Create a blank spreadsheet."""

    def executor(service: SheetsService) -> dict[str, Any]:
        return service.create(title=title)

    _run_sheets_action(
        ctx=ctx,
        action="sheets.create",
        resource_id_fallback=title,
        executor=executor,
    )


@sheets.command(name="append")
@click.option("--spreadsheet-id", required=True, type=str)
@click.option("--values", required=True, type=str)
@click.option("--range-name", default="Sheet1!A1", show_default=True, type=str)
@click.pass_context
def sheets_append(
    ctx: click.Context,
    spreadsheet_id: str,
    values: str,
    range_name: str,
) -> None:
    """Append one or more rows to a spreadsheet range."""
    try:
        parsed_values = _parse_values(values)
    except Exception as exc:
        _emit_sheets_result(
            action="sheets.append",
            result={
                "status": "error",
                "code": "GSHEETS_INVALID_VALUES",
                "message": str(exc),
            },
            resource_id_fallback=spreadsheet_id,
        )
        return

    def executor(service: SheetsService) -> dict[str, Any]:
        return service.append_row(
            spreadsheet_id=spreadsheet_id,
            values=parsed_values,
            range_name=range_name,
        )

    _run_sheets_action(
        ctx=ctx,
        action="sheets.append",
        resource_id_fallback=spreadsheet_id,
        executor=executor,
    )


@sheets.command(name="update")
@click.option("--spreadsheet-id", required=True, type=str)
@click.option("--range-name", required=True, type=str)
@click.option("--values", required=True, type=str)
@click.pass_context
def sheets_update(
    ctx: click.Context,
    spreadsheet_id: str,
    range_name: str,
    values: str,
) -> None:
    """Update a specific spreadsheet range."""
    try:
        parsed_values = _parse_values(values)
    except Exception as exc:
        _emit_sheets_result(
            action="sheets.update",
            result={
                "status": "error",
                "code": "GSHEETS_INVALID_VALUES",
                "message": str(exc),
            },
            resource_id_fallback=spreadsheet_id,
        )
        return

    def executor(service: SheetsService) -> dict[str, Any]:
        return service.update_range(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
            values=parsed_values,
        )

    _run_sheets_action(
        ctx=ctx,
        action="sheets.update",
        resource_id_fallback=spreadsheet_id,
        executor=executor,
    )


@sheets.command(name="read")
@click.option("--spreadsheet-id", required=True, type=str)
@click.option("--range-name", required=True, type=str)
@click.pass_context
def sheets_read(ctx: click.Context, spreadsheet_id: str, range_name: str) -> None:
    """Read values from a spreadsheet range."""

    def executor(service: SheetsService) -> dict[str, Any]:
        return service.read_range(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
        )

    _run_sheets_action(
        ctx=ctx,
        action="sheets.read",
        resource_id_fallback=spreadsheet_id,
        executor=executor,
    )


@calendar.command(name="list")
@click.option("--calendar-id", default="primary", show_default=True, type=str)
@click.option("--time-min", default=None, type=str)
@click.option("--max-results", default=10, show_default=True, type=click.IntRange(1, 250))
@click.pass_context
def calendar_list(
    ctx: click.Context,
    calendar_id: str,
    time_min: str | None,
    max_results: int,
) -> None:
    """List upcoming events."""

    def executor(service: CalendarService) -> dict[str, Any]:
        return service.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            max_results=max_results,
        )

    _run_calendar_action(
        ctx=ctx,
        action="calendar.list",
        resource_id_fallback=calendar_id,
        executor=executor,
    )


@calendar.command(name="create")
@click.option("--title", required=True, type=str)
@click.option("--start-time", required=True, type=str)
@click.option("--end-time", required=True, type=str)
@click.option("--description", default=None, type=str)
@click.option(
    "--attendees",
    default=None,
    type=str,
    help="JSON array of attendee emails, e.g. [\"a@example.com\"]",
)
@click.option("--add-meet/--no-add-meet", default=False, show_default=True)
@click.pass_context
def calendar_create(
    ctx: click.Context,
    title: str,
    start_time: str,
    end_time: str,
    description: str | None,
    attendees: str | None,
    add_meet: bool,
) -> None:
    """Create an event."""
    attendee_list: list[str] | None = None
    if attendees:
        try:
            attendee_list = _parse_string_list(attendees)
        except Exception as exc:
            _emit_calendar_result(
                action="calendar.create",
                result={
                    "status": "error",
                    "code": "GCALENDAR_INVALID_ATTENDEES",
                    "message": str(exc),
                },
                resource_id_fallback=title,
            )
            return

    def executor(service: CalendarService) -> dict[str, Any]:
        return service.create_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            attendees=attendee_list,
            add_meet=add_meet,
        )

    _run_calendar_action(
        ctx=ctx,
        action="calendar.create",
        resource_id_fallback=title,
        executor=executor,
    )


@calendar.command(name="delete")
@click.option("--event-id", required=True, type=str)
@click.pass_context
def calendar_delete(ctx: click.Context, event_id: str) -> None:
    """Delete an event."""

    def executor(service: CalendarService) -> dict[str, Any]:
        return service.delete_event(event_id=event_id)

    _run_calendar_action(
        ctx=ctx,
        action="calendar.delete",
        resource_id_fallback=event_id,
        executor=executor,
    )


@calendar.command(name="freebusy")
@click.option("--time-min", required=True, type=str)
@click.option("--time-max", required=True, type=str)
@click.option(
    "--calendar-ids",
    default=None,
    type=str,
    help="JSON array of calendar IDs, e.g. [\"primary\"]",
)
@click.pass_context
def calendar_freebusy(
    ctx: click.Context,
    time_min: str,
    time_max: str,
    calendar_ids: str | None,
) -> None:
    """Fetch busy blocks."""
    calendars: list[str] | None = None
    if calendar_ids:
        try:
            calendars = _parse_string_list(calendar_ids)
        except Exception as exc:
            _emit_calendar_result(
                action="calendar.freebusy",
                result={
                    "status": "error",
                    "code": "GCALENDAR_INVALID_CALENDAR_IDS",
                    "message": str(exc),
                },
                resource_id_fallback=f"{time_min}:{time_max}",
            )
            return

    def executor(service: CalendarService) -> dict[str, Any]:
        return service.get_free_busy(
            time_min=time_min,
            time_max=time_max,
            calendar_ids=calendars,
        )

    _run_calendar_action(
        ctx=ctx,
        action="calendar.freebusy",
        resource_id_fallback=f"{time_min}:{time_max}",
        executor=executor,
    )


@slides.command(name="create")
@click.option("--title", required=True, type=str)
@click.pass_context
def slides_create(ctx: click.Context, title: str) -> None:
    """Create a blank presentation."""

    def executor(service: SlidesService) -> dict[str, Any]:
        return service.create(title=title)

    _run_slides_action(
        ctx=ctx,
        action="slides.create",
        resource_id_fallback=title,
        executor=executor,
    )


@slides.command(name="read")
@click.option("--presentation-id", required=True, type=str)
@click.pass_context
def slides_read(ctx: click.Context, presentation_id: str) -> None:
    """Read text content from all slides."""

    def executor(service: SlidesService) -> dict[str, Any]:
        return service.get_content(presentation_id=presentation_id)

    _run_slides_action(
        ctx=ctx,
        action="slides.read",
        resource_id_fallback=presentation_id,
        executor=executor,
    )


@slides.command(name="add-slide")
@click.option("--presentation-id", required=True, type=str)
@click.option("--layout", default="TITLE_AND_BODY", show_default=True, type=str)
@click.pass_context
def slides_add_slide(ctx: click.Context, presentation_id: str, layout: str) -> None:
    """Add a new slide using a predefined layout."""

    def executor(service: SlidesService) -> dict[str, Any]:
        return service.add_slide(presentation_id=presentation_id, layout=layout)

    _run_slides_action(
        ctx=ctx,
        action="slides.add_slide",
        resource_id_fallback=presentation_id,
        executor=executor,
    )


@slides.command(name="replace")
@click.option("--presentation-id", required=True, type=str)
@click.option("--placeholder", required=True, type=str)
@click.option("--replacement", required=True, type=str)
@click.pass_context
def slides_replace(
    ctx: click.Context,
    presentation_id: str,
    placeholder: str,
    replacement: str,
) -> None:
    """Replace placeholder text throughout the presentation."""

    def executor(service: SlidesService) -> dict[str, Any]:
        return service.replace_text(
            presentation_id=presentation_id,
            placeholder=placeholder,
            replacement=replacement,
        )

    _run_slides_action(
        ctx=ctx,
        action="slides.replace",
        resource_id_fallback=presentation_id,
        executor=executor,
    )


@tasks.command(name="list-lists")
@click.pass_context
def tasks_list_lists(ctx: click.Context) -> None:
    """List available task lists."""

    def executor(service: TasksService) -> dict[str, Any]:
        return service.list_task_lists()

    _run_tasks_action(
        ctx=ctx,
        action="tasks.list_lists",
        resource_id_fallback="tasklists",
        executor=executor,
    )


@tasks.command(name="list")
@click.option("--list-id", default="@default", show_default=True, type=str)
@click.pass_context
def tasks_list(ctx: click.Context, list_id: str) -> None:
    """List tasks from a task list."""

    def executor(service: TasksService) -> dict[str, Any]:
        return service.list_tasks(list_id=list_id)

    _run_tasks_action(
        ctx=ctx,
        action="tasks.list",
        resource_id_fallback=list_id,
        executor=executor,
    )


@tasks.command(name="create")
@click.option("--title", required=True, type=str)
@click.option("--notes", default=None, type=str)
@click.option(
    "--due",
    default=None,
    type=str,
    help="RFC3339 timestamp, e.g. 2026-02-24T10:00:00Z",
)
@click.option("--list-id", default="@default", show_default=True, type=str)
@click.pass_context
def tasks_create(
    ctx: click.Context,
    title: str,
    notes: str | None,
    due: str | None,
    list_id: str,
) -> None:
    """Create a task."""

    def executor(service: TasksService) -> dict[str, Any]:
        return service.create_task(
            title=title,
            notes=notes,
            due=due,
            list_id=list_id,
        )

    _run_tasks_action(
        ctx=ctx,
        action="tasks.create",
        resource_id_fallback=title,
        executor=executor,
    )


@tasks.command(name="delete")
@click.option("--task-id", required=True, type=str)
@click.option("--list-id", default="@default", show_default=True, type=str)
@click.pass_context
def tasks_delete(ctx: click.Context, task_id: str, list_id: str) -> None:
    """Delete a task."""

    def executor(service: TasksService) -> dict[str, Any]:
        return service.delete_task(task_id=task_id, list_id=list_id)

    _run_tasks_action(
        ctx=ctx,
        action="tasks.delete",
        resource_id_fallback=task_id,
        executor=executor,
    )


@youtube.command(name="stats")
@click.pass_context
def youtube_stats(ctx: click.Context) -> None:
    """Get channel statistics for the authenticated account."""

    def executor(service: YouTubeService) -> dict[str, Any]:
        return service.get_channel_stats()

    _run_youtube_action(
        ctx=ctx,
        action="youtube.stats",
        resource_id_fallback="self",
        executor=executor,
    )


@youtube.command(name="upload")
@click.option(
    "--file-path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--title", required=True, type=str)
@click.option("--description", required=True, type=str)
@click.option("--category-id", default="27", show_default=True, type=str)
@click.option("--tags", default=None, type=str, help="JSON array of tags, e.g. [\"ai\",\"tutorial\"]")
@click.option(
    "--privacy",
    default="private",
    show_default=True,
    type=click.Choice(["private", "unlisted", "public"], case_sensitive=False),
)
@click.pass_context
def youtube_upload(
    ctx: click.Context,
    file_path: Path,
    title: str,
    description: str,
    category_id: str,
    tags: str | None,
    privacy: str,
) -> None:
    """Upload a video to YouTube."""
    tag_list: list[str] | None = None
    if tags:
        try:
            tag_list = _parse_string_list(tags)
        except Exception as exc:
            _emit_youtube_result(
                action="youtube.upload",
                result={
                    "status": "error",
                    "code": "GYOUTUBE_INVALID_TAGS",
                    "message": str(exc),
                },
                resource_id_fallback=str(file_path),
            )
            return

    def executor(service: YouTubeService) -> dict[str, Any]:
        return service.upload_video(
            file_path=str(file_path),
            title=title,
            description=description,
            category_id=category_id,
            tags=tag_list,
            privacy=privacy.lower(),
        )

    _run_youtube_action(
        ctx=ctx,
        action="youtube.upload",
        resource_id_fallback=str(file_path),
        executor=executor,
    )


@youtube.command(name="comments-list")
@click.option("--video-id", required=True, type=str)
@click.option("--limit", default=20, show_default=True, type=click.IntRange(1, 100))
@click.pass_context
def youtube_comments_list(ctx: click.Context, video_id: str, limit: int) -> None:
    """List top-level comment threads for a video."""

    def executor(service: YouTubeService) -> dict[str, Any]:
        return service.list_comments(video_id=video_id, max_results=limit)

    _run_youtube_action(
        ctx=ctx,
        action="youtube.comments_list",
        resource_id_fallback=video_id,
        executor=executor,
    )


@youtube.command(name="comments-reply")
@click.option("--parent-id", required=True, type=str)
@click.option("--text", required=True, type=str)
@click.pass_context
def youtube_comments_reply(ctx: click.Context, parent_id: str, text: str) -> None:
    """Reply to a YouTube comment."""

    def executor(service: YouTubeService) -> dict[str, Any]:
        return service.reply_to_comment(parent_id=parent_id, text=text)

    _run_youtube_action(
        ctx=ctx,
        action="youtube.comments_reply",
        resource_id_fallback=parent_id,
        executor=executor,
    )


@analytics.command(name="report")
@click.option("--property-id", required=True, type=str)
@click.option("--start-date", required=True, type=str)
@click.option("--end-date", required=True, type=str)
@click.option("--metrics", required=True, type=str, help="Comma-separated metrics, e.g. activeUsers,sessions")
@click.option("--dimensions", default="", type=str, help="Comma-separated dimensions, e.g. date,country")
@click.option("--limit", default=100, show_default=True, type=click.IntRange(1, 10000))
@click.pass_context
def analytics_report(
    ctx: click.Context,
    property_id: str,
    start_date: str,
    end_date: str,
    metrics: str,
    dimensions: str,
    limit: int,
) -> None:
    """Run a GA4 report via Analytics Data API."""
    metric_list = [item.strip() for item in metrics.split(",") if item.strip()]
    dimension_list = [item.strip() for item in dimensions.split(",") if item.strip()]

    def executor(service: AnalyticsService) -> dict[str, Any]:
        return service.run_report(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metric_list,
            dimensions=dimension_list or None,
            limit=limit,
        )

    _run_analytics_action(
        ctx=ctx,
        action="analytics.report",
        resource_id_fallback=property_id,
        executor=executor,
    )


@analytics.command(name="yt-private")
@click.option("--start-date", required=True, type=str)
@click.option("--end-date", required=True, type=str)
@click.option("--metrics", default="views,estimatedMinutesWatched,subscribersGained", show_default=True, type=str)
@click.option("--dimensions", default="day", show_default=True, type=str)
@click.option("--limit", default=30, show_default=True, type=click.IntRange(1, 200))
@click.pass_context
def analytics_yt_private(
    ctx: click.Context,
    start_date: str,
    end_date: str,
    metrics: str,
    dimensions: str,
    limit: int,
) -> None:
    """Run YouTube private analytics query."""

    def executor(service: YTAnalyticsService) -> dict[str, Any]:
        return service.query_private_metrics(
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            dimensions=dimensions,
            max_results=limit,
        )

    _run_yt_analytics_action(
        ctx=ctx,
        action="analytics.yt_private",
        resource_id_fallback=f"{start_date}:{end_date}",
        executor=executor,
    )


@analytics.command(name="yt-jobs")
@click.pass_context
def analytics_yt_jobs(ctx: click.Context) -> None:
    """List YouTube reporting jobs."""

    def executor(service: YTAnalyticsService) -> dict[str, Any]:
        return service.list_reporting_jobs()

    _run_yt_analytics_action(
        ctx=ctx,
        action="analytics.yt_jobs",
        resource_id_fallback="jobs",
        executor=executor,
    )


@search_console.command(name="sites")
@click.pass_context
def search_console_sites(ctx: click.Context) -> None:
    """List verified Search Console sites."""

    def executor(service: SearchConsoleService) -> dict[str, Any]:
        return service.list_sites()

    _run_search_console_action(
        ctx=ctx,
        action="search_console.sites",
        resource_id_fallback="sites",
        executor=executor,
    )


@search_console.command(name="performance")
@click.option("--site-url", required=True, type=str)
@click.option("--start-date", required=True, type=str)
@click.option("--end-date", required=True, type=str)
@click.option("--dimensions", default='["query"]', show_default=True, type=str, help="JSON array of dimensions")
@click.option("--limit", default=25, show_default=True, type=click.IntRange(1, 25000))
@click.option("--search-type", default="web", show_default=True, type=str)
@click.pass_context
def search_console_performance(
    ctx: click.Context,
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: str,
    limit: int,
    search_type: str,
) -> None:
    """Query Search Console performance rows."""
    try:
        dims = _parse_string_list(dimensions)
    except Exception as exc:
        _emit_service_result(
            service_name="search-console",
            action="search_console.performance",
            result={"status": "error", "code": "GSC_INVALID_DIMENSIONS", "message": str(exc)},
            resource_id_fallback=site_url,
            default_code="GSC_UNKNOWN_ERROR",
            default_message="Unknown Search Console error",
            resource_keys=["site_url", "resource_id"],
        )
        return

    def executor(service: SearchConsoleService) -> dict[str, Any]:
        return service.query_performance(
            site_url=site_url,
            start_date=start_date,
            end_date=end_date,
            dimensions=dims,
            row_limit=limit,
            search_type=search_type,
        )

    _run_search_console_action(
        ctx=ctx,
        action="search_console.performance",
        resource_id_fallback=site_url,
        executor=executor,
    )


@forms.command(name="create")
@click.option("--title", required=True, type=str)
@click.option("--document-title", default=None, type=str)
@click.pass_context
def forms_create(ctx: click.Context, title: str, document_title: str | None) -> None:
    """Create a Google Form."""

    def executor(service: FormsService) -> dict[str, Any]:
        return service.create_form(title=title, document_title=document_title)

    _run_forms_action(
        ctx=ctx,
        action="forms.create",
        resource_id_fallback=title,
        executor=executor,
    )


@forms.command(name="responses")
@click.option("--form-id", required=True, type=str)
@click.option("--limit", default=50, show_default=True, type=click.IntRange(1, 5000))
@click.pass_context
def forms_responses(ctx: click.Context, form_id: str, limit: int) -> None:
    """List form responses."""

    def executor(service: FormsService) -> dict[str, Any]:
        return service.list_responses(form_id=form_id, page_size=limit)

    _run_forms_action(
        ctx=ctx,
        action="forms.responses",
        resource_id_fallback=form_id,
        executor=executor,
    )


@ads.command(name="overview")
@click.option("--customer-id", required=True, type=str)
@click.option("--login-customer-id", default=None, type=str)
@click.option("--limit", default=20, show_default=True, type=click.IntRange(1, 500))
@click.pass_context
def ads_overview(
    ctx: click.Context,
    customer_id: str,
    login_customer_id: str | None,
    limit: int,
) -> None:
    """Fetch campaign and budget overview."""

    def executor(service: AdsService) -> dict[str, Any]:
        return service.campaign_overview(
            customer_id=customer_id,
            login_customer_id=login_customer_id,
            limit=limit,
        )

    _run_ads_action(
        ctx=ctx,
        action="ads.overview",
        resource_id_fallback=customer_id,
        executor=executor,
    )


@news.command(name="search")
@click.argument("query", type=str)
@click.option("--limit", default=10, show_default=True, type=click.IntRange(1, 50))
def news_search(query: str, limit: int) -> None:
    """Search real-time news through Apify actor integration."""

    def executor(service: NewsService) -> dict[str, Any]:
        return service.search(query=query, limit=limit)

    _run_news_action(
        action="news.search",
        resource_id_fallback=query,
        executor=executor,
    )


@news.command(name="trending")
@click.option("--limit", default=10, show_default=True, type=click.IntRange(1, 50))
def news_trending(limit: int) -> None:
    """Fetch trending news headlines through Apify actor integration."""

    def executor(service: NewsService) -> dict[str, Any]:
        return service.trending(limit=limit)

    _run_news_action(
        action="news.trending",
        resource_id_fallback="trending",
        executor=executor,
    )


@maps.command(name="places-search")
@click.option("--query", required=True, type=str)
@click.option("--limit", default=5, show_default=True, type=click.IntRange(1, 20))
def maps_places_search(query: str, limit: int) -> None:
    """Search places using Google Places (New)."""

    def executor(service: MapsRoutesService) -> dict[str, Any]:
        return service.places_search_text(query=query, limit=limit)

    _run_maps_action(
        action="maps.places_search",
        resource_id_fallback=query,
        executor=executor,
    )


@maps.command(name="directions")
@click.option("--origin", required=True, type=str)
@click.option("--destination", required=True, type=str)
@click.option("--mode", default="driving", show_default=True, type=str)
def maps_directions(origin: str, destination: str, mode: str) -> None:
    """Get route directions between origin and destination."""

    def executor(service: MapsRoutesService) -> dict[str, Any]:
        return service.directions(origin=origin, destination=destination, mode=mode)

    _run_maps_action(
        action="maps.directions",
        resource_id_fallback=f"{origin}->{destination}",
        executor=executor,
    )


@maps.command(name="distance-matrix")
@click.option("--origins", required=True, type=str, help="JSON array of origin strings")
@click.option("--destinations", required=True, type=str, help="JSON array of destination strings")
@click.option("--mode", default="driving", show_default=True, type=str)
def maps_distance_matrix(origins: str, destinations: str, mode: str) -> None:
    """Get pairwise distance matrix."""
    try:
        origin_list = _parse_string_list(origins)
        destination_list = _parse_string_list(destinations)
    except Exception as exc:
        _emit_service_result(
            service_name="maps",
            action="maps.distance_matrix",
            result={"status": "error", "code": "GMAPS_INVALID_LOCATIONS", "message": str(exc)},
            resource_id_fallback="matrix",
            default_code="GMAPS_UNKNOWN_ERROR",
            default_message="Unknown Maps error",
            resource_keys=["resource_id"],
        )
        return

    def executor(service: MapsRoutesService) -> dict[str, Any]:
        return service.distance_matrix(origins=origin_list, destinations=destination_list, mode=mode)

    _run_maps_action(
        action="maps.distance_matrix",
        resource_id_fallback="matrix",
        executor=executor,
    )


@env.command(name="weather")
@click.option("--lat", required=True, type=float)
@click.option("--lng", required=True, type=float)
def env_weather(lat: float, lng: float) -> None:
    """Get current weather context."""

    def executor(service: EnvContextService) -> dict[str, Any]:
        return service.weather_current(latitude=lat, longitude=lng)

    _run_env_action(
        action="env.weather",
        resource_id_fallback=f"{lat},{lng}",
        executor=executor,
    )


@env.command(name="timezone")
@click.option("--lat", required=True, type=float)
@click.option("--lng", required=True, type=float)
def env_timezone(lat: float, lng: float) -> None:
    """Get time zone context."""

    def executor(service: EnvContextService) -> dict[str, Any]:
        return service.time_zone(latitude=lat, longitude=lng)

    _run_env_action(
        action="env.timezone",
        resource_id_fallback=f"{lat},{lng}",
        executor=executor,
    )


@env.command(name="route-optimize")
@click.option("--origin", required=True, type=str, help='JSON object: {"lat": ..., "lng": ...}')
@click.option("--stops", required=True, type=str, help='JSON array: [{"lat":...,"lng":...}]')
@click.option("--round-trip/--no-round-trip", default=False, show_default=True)
def env_route_optimize(origin: str, stops: str, round_trip: bool) -> None:
    """Optimize stop ordering using nearest-neighbor heuristic."""
    try:
        origin_coord = _parse_coordinate(origin)
        stop_coords = _parse_coordinate_list(stops)
    except Exception as exc:
        _emit_service_result(
            service_name="env",
            action="env.route_optimize",
            result={"status": "error", "code": "GENV_INVALID_COORDINATES", "message": str(exc)},
            resource_id_fallback="route",
            default_code="GENV_UNKNOWN_ERROR",
            default_message="Unknown Env Context error",
            resource_keys=["resource_id"],
        )
        return

    def executor(service: EnvContextService) -> dict[str, Any]:
        return service.route_optimize(origin=origin_coord, stops=stop_coords, round_trip=round_trip)

    _run_env_action(
        action="env.route_optimize",
        resource_id_fallback="route",
        executor=executor,
    )


@chat.command(name="list-spaces")
@click.option("--page-size", default=20, show_default=True, type=click.IntRange(1, 1000))
@click.pass_context
def chat_list_spaces(ctx: click.Context, page_size: int) -> None:
    """List spaces for the current account."""

    def executor(service: ChatService) -> dict[str, Any]:
        return service.list_spaces(page_size=page_size)

    _run_chat_action(
        ctx=ctx,
        action="chat.list_spaces",
        resource_id_fallback=str(page_size),
        executor=executor,
    )


@chat.command(name="send")
@click.option("--space-name", required=True, type=str)
@click.option("--text", required=True, type=str)
@click.pass_context
def chat_send(ctx: click.Context, space_name: str, text: str) -> None:
    """Send a message to a Chat space."""

    def executor(service: ChatService) -> dict[str, Any]:
        return service.send_message(space_name=space_name, text=text)

    _run_chat_action(
        ctx=ctx,
        action="chat.send",
        resource_id_fallback=space_name,
        executor=executor,
    )


@chat.command(name="get-space")
@click.option("--space-name", required=True, type=str)
@click.pass_context
def chat_get_space(ctx: click.Context, space_name: str) -> None:
    """Get details for a specific Chat space."""

    def executor(service: ChatService) -> dict[str, Any]:
        return service.get_space(space_name=space_name)

    _run_chat_action(
        ctx=ctx,
        action="chat.get_space",
        resource_id_fallback=space_name,
        executor=executor,
    )


@vault.command(name="set")
@click.argument("key", type=str)
@click.argument("value_source", type=str)
def vault_set(key: str, value_source: str) -> None:
    """Encrypt and store a value from a file path or inline string."""

    def executor(vault_store: Any) -> dict[str, Any]:
        result = vault_store.set_from_file_or_string(key=key, source=value_source)
        return {
            "status": "success",
            "key": key,
            "source_type": result.get("source_type"),
            "source_ref": result.get("source_ref"),
            "vault_path": str(VAULT_DATA_PATH),
        }

    _run_vault_action(
        action="vault.set",
        resource_id_fallback=key,
        executor=executor,
    )


@vault.command(name="get")
@click.argument("key", type=str)
def vault_get(key: str) -> None:
    """Decrypt and return a vault value by key."""

    def executor(vault_store: Any) -> dict[str, Any]:
        value = vault_store.get_value(key=key)
        return {
            "status": "success",
            "key": key,
            "value": value,
            "vault_path": str(VAULT_DATA_PATH),
        }

    _run_vault_action(
        action="vault.get",
        resource_id_fallback=key,
        executor=executor,
    )


@vault.command(name="list")
def vault_list() -> None:
    """List stored vault keys without exposing values."""

    def executor(vault_store: Any) -> dict[str, Any]:
        keys = vault_store.list_keys()
        return {
            "status": "success",
            "keys": keys,
            "count": len(keys),
            "vault_path": str(VAULT_DATA_PATH),
        }

    _run_vault_action(
        action="vault.list",
        resource_id_fallback="all",
        executor=executor,
    )


@sandbox.command(name="run")
@click.argument("command", type=str)
@click.option("--allow-network", is_flag=True, default=False, show_default=True)
@click.pass_context
def sandbox_run(ctx: click.Context, command: str, allow_network: bool) -> None:
    """Run a shell command in an ephemeral container sandbox."""
    use_sandbox = bool(ctx.obj.get("use_sandbox", True))
    _run_sandbox_action(
        action="sandbox.run",
        resource_id_fallback=command,
        command=command,
        use_sandbox=use_sandbox,
        allow_network=allow_network,
    )


@ltr.command(name="setup")
@click.option(
    "--config",
    "config_path",
    default=Path("credentials.json"),
    show_default=True,
    type=click.Path(dir_okay=False, path_type=Path),
)
def setup(config_path: Path) -> None:
    """Initialize OAuth credentials and local token cache."""
    logger = LTRAuditLogger()
    auth = LTRAuth(config_path=config_path, token_path=LOCAL_TOKEN_PATH)

    try:
        credentials = auth.get_credentials()
        logger.log_event(
            service="core",
            action="ltr.setup",
            status="success",
            resource_id=str(auth.token_path),
        )
        emit(
            {
                "ok": True,
                "service": "core",
                "action": "ltr.setup",
                "data": {
                    "token_path": str(auth.token_path),
                    "scopes": LTRAuth.SCOPES,
                    "valid": credentials.valid,
                },
                "error": None,
            }
        )
    except Exception as exc:
        logger.log_event(
            service="core",
            action="ltr.setup",
            status="error",
            resource_id=str(auth.token_path),
        )
        emit(
            {
                "ok": False,
                "service": "core",
                "action": "ltr.setup",
                "data": {},
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            },
            exit_code=1,
        )


if __name__ == "__main__":
    _require_secure_environment()
    ltr()
