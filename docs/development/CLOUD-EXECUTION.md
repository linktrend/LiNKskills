# Cloud and CI execution environment

This document is the ENV-00 contract for a reproducible LiNKskills development
install. It pins public-PyPI test/dev artifacts. It does not pin production
runtime images, Node, or product package versions.

## Attested compiler (ENV-00 cloud worker)

| Fact | Value |
|---|---|
| OS | Ubuntu 24.04.4 LTS (`noble`) |
| Kernel / arch | Linux x86_64 (`x86_64`) |
| Interpreter | CPython 3.12.3 (`/usr/bin/python3.12`) |
| System pip | 24.0 (`python3 -m pip`) |
| Disposable compiler pip | 24.3.1 (required by pip-tools 7.4.1) |
| Lock generator | pip-tools 7.4.1 (`pip-compile --generate-hashes`) |
| Headers / venv | `python3.12-venv` and `python3.12-dev` already present |

Python 3.11 was not available in this VM's apt cache. Repository packages
declare `requires-python = ">=3.11"`, so 3.12.3 is a valid worker interpreter.
Protected CI remains the compatibility authority: `ubuntu-24.04-arm` with
Python 3.11. The lock records SHA-256 hashes for every PyPI file of each
pinned version (including `cp311` / `aarch64` wheels where published).

Node 22.14.0 may be present on the cloud image. This packet does not require
Node or a JavaScript package manager: there is no Node package manifest.

## Hash-locked public dependencies

Source ranges live in `requirements-dev.txt`. Exact versions and artifact
hashes live in `requirements-dev.lock`.

```bash
python3 -m venv .venv
source .venv/bin/activate   # nvm PATH / venv activation may not persist
python -m pip install --require-hashes -r requirements-dev.lock
```

Do not `pip install -r requirements-dev.txt` in CI. That path is an unbounded
resolver and is retained only as the compile input.

### Stable regeneration

Use a disposable compiler venv (do not add pip-tools to product dependencies):

```bash
python3 -m venv /tmp/linkskills-lock-compiler
/tmp/linkskills-lock-compiler/bin/python -m pip install 'pip==24.3.1' 'pip-tools==7.4.1'
/tmp/linkskills-lock-compiler/bin/pip-compile \
  --generate-hashes --allow-unsafe --no-emit-index-url --no-strip-extras \
  --output-file requirements-dev.lock requirements-dev.txt
```

Two consecutive compiles to the same output path must be byte-identical.
Comment-header flags inserted by pip-tools (`--cert=None`, output path) are
not part of the requirement stanza digest. Do not silently bump pip past the
pip-tools-supported series; pip 26 removed `pip._internal.utils.compat.stdlib_pkgs`
and breaks pip-tools 7.4.1.

## Local-package-before-umbrella installation order

Eight installable path packages must be installed **before** the root umbrella
`linkskills` meta-package. After the hash-locked PyPI install, use `--no-deps`
so local extras cannot bypass `--require-hashes`:

1. `pip install --no-deps -e packages/core`
2. `pip install --no-deps -e packages/tool_runtime`
3. `pip install --no-deps -e packages/gateway`
4. `pip install --no-deps -e "packages/gateway[postgres]"`
5. `pip install --no-deps -e packages/client`
6. `pip install --no-deps -e packages/mcp_server`
7. `pip install --no-deps -e packages/librarian_domain`
8. `pip install --no-deps -e packages/publisher`
9. `pip install --no-deps -e packages/eval_runner`
10. `pip install --no-deps -e .`  (umbrella; last)

`packages/gateway[postgres]` is the optional extra of step 3, not a ninth
distribution. The eight distributions are: `linkskills-core`,
`linkskills-tool-runtime`, `linkskills-gateway`, `linkskills-client`,
`linkskills-mcp`, `linkskills-librarian`, `linkskills-publisher`,
`linkskills-eval-runner`.

## PYTHONPATH-only packages

`packages/contracts` and `packages/persistence` have no `pyproject.toml` and
are **not** pip-installable. Tests and workers must put them on `PYTHONPATH`
(as CI already does for contracts, plus persistence when a store test needs
it). Do not add them to `requirements-dev.lock`.

Current catalog/unit PYTHONPATH used by CI:

```text
packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:.
```

## What this packet does not change

Product `packages/*/pyproject.toml` dependencies, Skills, migrations, deploy
files, consumer configuration, credentials, providers, Server 01, and the IDE
managed core are out of scope. Production data and GSM values must not enter
the cloud VM.
