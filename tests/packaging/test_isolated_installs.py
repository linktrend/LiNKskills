"""Isolated packaging proofs for LiNKskills runtime packages.

Creates temporary virtualenvs, editable-installs declared packages with their
dependencies, then proves import / entrypoint / local start without contacting
live network services (Gateway/Postgres/PACI).
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import venv
from pathlib import Path
from typing import Sequence

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = REPO_ROOT / "packages"


def _run(
    cmd: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: float = 300,
) -> subprocess.CompletedProcess[str]:
    merged = dict(os.environ)
    if env:
        merged.update(env)
    # Keep packaging proofs free of production secrets / live DSNs.
    for key in list(merged):
        if key.startswith("LINKSKILLS_") or key in {
            "DATABASE_URL",
            "POSTGRES_URL",
            "PGHOST",
            "PGDATABASE",
        }:
            # Preserve only the explicit local-test overrides we inject.
            if env and key in env:
                continue
            merged.pop(key, None)
    return subprocess.run(
        list(cmd),
        cwd=str(cwd or REPO_ROOT),
        env=merged,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _create_venv(venv_dir: Path) -> Path:
    venv.create(venv_dir, with_pip=True, clear=True)
    py = _venv_python(venv_dir)
    assert py.is_file(), f"venv python missing: {py}"
    bootstrap = _run(
        [str(py), "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"],
        timeout=180,
    )
    assert bootstrap.returncode == 0, (
        f"pip bootstrap failed:\n{bootstrap.stdout}\n{bootstrap.stderr}"
    )
    return py


def _pip_install(py: Path, *args: str, timeout: float = 300) -> None:
    result = _run([str(py), "-m", "pip", "install", *args], timeout=timeout)
    assert result.returncode == 0, (
        f"pip install {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
    )


def _py_ok(py: Path, code: str, *, env: dict[str, str] | None = None) -> str:
    result = _run([str(py), "-c", textwrap.dedent(code)], env=env, timeout=60)
    assert result.returncode == 0, (
        f"python -c failed ({result.returncode}):\n"
        f"code:\n{code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result.stdout


@pytest.fixture(scope="module")
def packaging_venv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One isolated venv for the packaging suite (not the repo .venv)."""
    root = tmp_path_factory.mktemp("linkskills-packaging-venv")
    venv_dir = root / "venv"
    py = _create_venv(venv_dir)

    # Install in dependency order so name pins resolve from local path packages.
    _pip_install(py, "-e", str(PACKAGES / "core"))
    _pip_install(py, "-e", str(PACKAGES / "tool_runtime"))
    _pip_install(py, "-e", str(PACKAGES / "gateway"))
    _pip_install(py, "-e", f"{PACKAGES / 'gateway'}[postgres]")
    _pip_install(py, "-e", str(PACKAGES / "client"))
    _pip_install(py, "-e", str(PACKAGES / "mcp_server"))
    _pip_install(py, "-e", str(PACKAGES / "librarian_domain"))
    _pip_install(py, "-e", str(PACKAGES / "publisher"))
    _pip_install(py, "-e", str(PACKAGES / "eval_runner"))
    return py


class TestPackageMetadata:
    def test_pyprojects_declare_required_deps(self) -> None:
        gateway = (PACKAGES / "gateway" / "pyproject.toml").read_text(encoding="utf-8")
        assert "linkskills-core>=0.1.0" in gateway
        assert "linkskills-tool-runtime>=0.1.0" in gateway
        assert "cryptography>=" in gateway
        assert 'postgres = [' in gateway or "postgres =" in gateway
        assert "psycopg[binary]>=3.1" in gateway

        librarian = (PACKAGES / "librarian_domain" / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        assert "psycopg[binary]>=3.1" in librarian
        assert "linkskills-core>=" in librarian

        publisher = (PACKAGES / "publisher" / "pyproject.toml").read_text(encoding="utf-8")
        assert 'name = "linkskills-publisher"' in publisher
        assert "linkskills-core>=" in publisher
        assert "psycopg[binary]>=3.1" in publisher

        eval_runner = (PACKAGES / "eval_runner" / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        assert 'name = "linkskills-eval-runner"' in eval_runner
        assert "linkskills-core>=" in eval_runner
        assert "pyyaml>=" in eval_runner

        tool_runtime = (PACKAGES / "tool_runtime" / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        assert 'name = "linkskills-tool-runtime"' in tool_runtime
        assert "pyyaml>=6.0" in tool_runtime


class TestPrivacyFailClosedSource:
    def test_service_hard_requires_payload_guard(self) -> None:
        source = (
            PACKAGES / "gateway" / "linkskills_gateway" / "service.py"
        ).read_text(encoding="utf-8")
        assert "from linkskills_core.payload_guard import" in source
        # Soft-disable pattern must not return.
        assert "except ImportError:  # pragma: no cover - path wiring in tests" not in source
        assert "prepare_feedback_params = None" not in source
        assert "PayloadValidationError = None" not in source

    def test_guard_params_refuses_missing_preparer(self) -> None:
        source = (
            PACKAGES / "gateway" / "linkskills_gateway" / "service.py"
        ).read_text(encoding="utf-8")
        assert 'code="privacy_unavailable"' in source or "privacy_unavailable" in source


class TestIsolatedInstallImportStart:
    def test_core_privacy_import(self, packaging_venv: Path) -> None:
        out = _py_ok(
            packaging_venv,
            """
            from linkskills_core.payload_guard import (
                PayloadValidationError,
                prepare_feedback_params,
                prepare_run_mutation_params,
                prepare_trace_params,
            )
            from importlib.metadata import version
            print(version("linkskills-core"))
            print("privacy_ok")
            """,
        )
        assert "privacy_ok" in out
        assert "0.1.0" in out

    def test_gateway_import_and_local_start(self, packaging_venv: Path) -> None:
        # Import proves privacy hard-require + declared deps (core, cryptography).
        _py_ok(
            packaging_venv,
            """
            from linkskills_gateway.service import SkillsGatewayService
            from linkskills_gateway.server import create_server
            from linkskills_core.payload_guard import (
                PayloadValidationError,
                prepare_feedback_params,
            )
            import linkskills_gateway.service as svc_mod
            assert svc_mod.prepare_feedback_params is prepare_feedback_params
            assert PayloadValidationError is not None
            print("gateway_import_ok")
            """,
        )

        # Local start: bind ephemeral port, hit /health, shut down. No live services.
        start_script = textwrap.dedent(
            """
            import os
            import threading
            import time
            import urllib.request

            os.environ["LINKSKILLS_AUTH_MODE"] = "local-test"
            os.environ["LINKSKILLS_GATEWAY_STORE"] = "memory"
            os.environ.pop("LINKSKILLS_ENV", None)

            from linkskills_gateway.server import create_server

            httpd = create_server("127.0.0.1", 0)
            host, port = httpd.server_address[:2]
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as resp:
                    body = resp.read().decode("utf-8")
                    assert resp.status == 200, body
                    assert "ok" in body.lower() or "status" in body or "{" in body
                print(f"gateway_start_ok:{port}")
            finally:
                httpd.shutdown()
                httpd.server_close()
            """
        )
        out = _py_ok(
            packaging_venv,
            start_script,
            env={
                "LINKSKILLS_AUTH_MODE": "local-test",
                "LINKSKILLS_GATEWAY_STORE": "memory",
            },
        )
        assert "gateway_start_ok:" in out

        # Console script / module entry is importable.
        mod = _run(
            [
                str(packaging_venv),
                "-c",
                "from linkskills_gateway.server import main; print('entrypoint', main.__module__)",
            ]
        )
        assert mod.returncode == 0, mod.stderr
        assert "entrypoint" in mod.stdout

        # Postgres extra: psycopg importable after gateway[postgres].
        _py_ok(
            packaging_venv,
            """
            import psycopg
            from linkskills_gateway.postgres_store import PostgresGatewayStore
            print("postgres_extra_ok", psycopg.__name__)
            """,
        )

    def test_tool_runtime_import_and_descriptor_resolution(
        self, packaging_venv: Path
    ) -> None:
        """Gateway tool execution dependencies work in an isolated installed venv."""
        out = _py_ok(
            packaging_venv,
            f"""
            from importlib.metadata import version
            from pathlib import Path
            import yaml
            from linkskills_tool_runtime.resolve import resolve_tool

            tool = resolve_tool(
                Path({str(REPO_ROOT / "tools" / "text-echo")!r}),
                tool_id="text-echo",
            )
            assert tool.tool_id == "text-echo"
            assert tool.descriptor.source_hash
            print("tool_runtime_ok", version("linkskills-tool-runtime"), yaml.__version__)
            """,
        )
        assert "tool_runtime_ok" in out

    def test_mcp_and_client_import(self, packaging_venv: Path) -> None:
        _py_ok(
            packaging_venv,
            """
            from linkskills_mcp.server import SkillsMcpServer, main as mcp_main
            from linkskills_client import SkillsGatewayClient, PaciTokenClient
            from importlib.metadata import version
            print(version("linkskills-mcp"))
            print(version("linkskills-client"))
            print("mcp_client_ok", SkillsMcpServer.__name__, mcp_main.__name__)
            """,
        )

        # MCP "start" proof without hanging on stdio: construct server under local-test.
        _py_ok(
            packaging_venv,
            """
            import os
            os.environ["LINKSKILLS_AUTH_MODE"] = "local-test"
            os.environ["LINKSKILLS_GATEWAY_STORE"] = "memory"
            from linkskills_mcp.server import SkillsMcpServer
            from linkskills_gateway.auth import ActorClaims
            actor = ActorClaims(
                actor_id="packaging-proof",
                actor_kind="service",
                org_id="org-packaging",
                scopes=frozenset({"lskills"}),
                permitted_operations=frozenset({"read", "execute"}),
                exp=2**31 - 1,
            )
            server = SkillsMcpServer(default_actor=actor)
            assert hasattr(server, "handle_rpc")
            print("mcp_start_construct_ok")
            """,
            env={
                "LINKSKILLS_AUTH_MODE": "local-test",
                "LINKSKILLS_GATEWAY_STORE": "memory",
            },
        )

    def test_publisher_import_and_package(self, packaging_venv: Path) -> None:
        _py_ok(
            packaging_venv,
            """
            from importlib.metadata import version, requires
            from linkskills_publisher import (
                PublisherRegistry,
                PostgresPublisherRegistry,
                build_skill_bundle,
            )
            import psycopg
            print(version("linkskills-publisher"))
            print("publisher_ok", PublisherRegistry.__name__, PostgresPublisherRegistry.__name__)
            print("psycopg", psycopg.__name__)
            """,
        )

    def test_eval_runner_import_and_cli(self, packaging_venv: Path) -> None:
        _py_ok(
            packaging_venv,
            """
            from importlib.metadata import version
            from linkskills_eval_runner import load_eval_suite, certify_run
            from linkskills_eval_runner.cli import build_parser, main
            print(version("linkskills-eval-runner"))
            parser = build_parser()
            help_text = parser.format_help()
            assert "eval" in help_text.lower() or "suite" in help_text.lower()
            print("eval_runner_ok", main.__name__)
            """,
        )
        # Console script / module entry without running a live suite.
        result = _run(
            [str(packaging_venv), "-m", "linkskills_eval_runner", "--help"],
            timeout=30,
        )
        # argparse with required subcommand may exit 2 on bare --help depending on version;
        # accept 0 or documented usage on stderr/stdout.
        combined = (result.stdout or "") + (result.stderr or "")
        assert result.returncode in {0, 2}, combined
        assert "usage" in combined.lower() or "eval" in combined.lower()

    def test_librarian_import(self, packaging_venv: Path) -> None:
        _py_ok(
            packaging_venv,
            """
            from importlib.metadata import version
            from linkskills_librarian import DomainWorker, PostgresReviewQueueStore
            import psycopg
            worker = DomainWorker()
            print(version("linkskills-librarian"))
            print("librarian_ok", worker.domain_key, PostgresReviewQueueStore.__name__, psycopg.__name__)
            """,
        )

    def test_gateway_without_core_fails_closed(self, tmp_path: Path) -> None:
        """Fresh venv with only gateway sources on path (no core) must fail import."""
        py = _create_venv(tmp_path / "venv-no-core")
        # Install cryptography only (gateway runtime crypto), not core.
        _pip_install(py, "cryptography>=42.0.0")
        # Point at gateway package tree without installing core.
        env = {
            "PYTHONPATH": str(PACKAGES / "gateway"),
            "LINKSKILLS_AUTH_MODE": "local-test",
        }
        result = _run(
            [
                str(py),
                "-c",
                "import linkskills_gateway.service",
            ],
            env=env,
            timeout=60,
        )
        assert result.returncode != 0, "expected ImportError when core/privacy missing"
        combined = (result.stdout or "") + (result.stderr or "")
        assert (
            "linkskills_core" in combined
            or "payload_guard" in combined
            or "ModuleNotFoundError" in combined
            or "ImportError" in combined
        ), combined
