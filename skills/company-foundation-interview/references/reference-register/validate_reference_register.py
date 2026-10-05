#!/usr/bin/env python3
"""Validate reference-register structure and every active packaged content locator."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover - diagnostic for operator environment
    raise SystemExit("jsonschema is required for register validation (JSON Schema draft 2020-12)") from exc


HEX256 = re.compile(r"^[a-f0-9]{64}$")
REGISTER_FILES = ("knowledge-register.json", "template-register.json")


def fail(message: str) -> None:
    raise ValueError(message)


def safe_file(skill_root: Path, locator: Any, context: str) -> tuple[Path, bytes]:
    if not isinstance(locator, str) or not locator:
        fail(f"{context}: locator must be a non-empty string")
    rel = Path(locator)
    if rel.is_absolute() or ".." in rel.parts or "." in rel.parts or rel.as_posix() != locator or "\\" in locator or "\x00" in locator:
        fail(f"{context}: unsafe or ambiguous skill-relative path {locator!r}")
    candidate = skill_root / rel
    cursor = skill_root
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            fail(f"{context}: symlink path is not an authoritative locator: {locator!r}")
    try:
        resolved = candidate.resolve(strict=True)
        root = skill_root.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        fail(f"{context}: missing or out-of-root path {locator!r}: {exc}")
    if not resolved.is_file():
        fail(f"{context}: path is not a regular file: {locator!r}")
    return resolved, resolved.read_bytes()


def verify_bytes(skill_root: Path, record: dict[str, Any], context: str) -> bytes:
    path, data = safe_file(skill_root, record.get("path"), context)
    expected_hash = record.get("sha256")
    expected_bytes = record.get("bytes")
    actual_hash = hashlib.sha256(data).hexdigest()
    if not isinstance(expected_hash, str) or not HEX256.fullmatch(expected_hash):
        fail(f"{context}: invalid sha256")
    if actual_hash != expected_hash:
        fail(f"{context}: sha256 mismatch for {record['path']}: expected {expected_hash}, got {actual_hash}")
    if isinstance(expected_bytes, bool) or not isinstance(expected_bytes, int) or expected_bytes != len(data):
        fail(f"{context}: byte-count mismatch for {record['path']}: expected {expected_bytes}, got {len(data)}")
    return data


def flatten_chunks(skill_root: Path, row: dict[str, Any], context: str) -> list[dict[str, Any]]:
    chunks = row["disclosure_chunks"]
    if isinstance(chunks, list):
        return chunks
    manifest_path, payload = safe_file(skill_root, chunks.get("manifest"), f"{context}.disclosure_chunks.manifest")
    try:
        manifest_rows = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"{context}: invalid chunk manifest: {exc}")
    if not isinstance(manifest_rows, list):
        fail(f"{context}: chunk manifest must contain an array")
    if chunks.get("count") != len(manifest_rows):
        fail(f"{context}: manifest count mismatch at {manifest_path}")
    return manifest_rows


def disclosure_body(chunk_bytes: bytes, context: str) -> str:
    try:
        chunk_text = chunk_bytes.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        fail(f"{context}: disclosure chunk is not UTF-8 text: {exc}")
    lines = chunk_text.splitlines(keepends=True)
    end = None
    for index, line in enumerate(lines):
        if line.startswith("Source/reference only;"):
            end = index + 1
            while end < len(lines) and not lines[end].strip():
                end += 1
            break
    if end is None:
        fail(f"{context}: generated disclosure wrapper is missing the source/reference boundary")
    body = "".join(lines[end:])
    if not body.strip():
        fail(f"{context}: disclosure chunk has an empty body and is not usable source content")
    return body


def validate_chunk_source_relationship(source_text: str, chunk_body: str, cursor: int, context: str) -> int:
    normalized_source = source_text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_body = chunk_body.replace("\r\n", "\n").replace("\r", "\n")
    start = normalized_source.find(normalized_body, cursor)
    if start < 0:
        fail(f"{context}: disclosure body is not an ordered substring of its declared packaged text source")
    return start + len(normalized_body)


def validate_one_register(skill_root: Path, register_path: Path, schema: dict[str, Any], register: dict[str, Any] | None = None) -> dict[str, Any]:
    if register is None:
        try:
            register = json.loads(register_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"{register_path}: cannot read register JSON: {exc}")
    errors = sorted(Draft202012Validator(schema).iter_errors(register), key=lambda e: list(map(str, e.path)))
    if errors:
        first = errors[0]
        fail(f"{register_path.name}: schema error at {list(first.path)}: contract violation ({len(errors)} total)")

    expected_class = "knowledge" if register_path.name.startswith("knowledge-") else "template"
    unique_active_paths: dict[str, tuple[str, str]] = {}
    chunks_total = 0
    packaged_total = 0
    classes: Counter[str] = Counter()
    record_kinds: Counter[str] = Counter()
    for index, row in enumerate(register["items"]):
        context = f"{register_path.name}[{index}]"
        if row["resource_class"] != expected_class:
            fail(f"{context}: resource_class does not match register")
        source_row = row.get("source_register_row")
        if source_row is not None and (isinstance(source_row, bool) or not isinstance(source_row, int) or source_row < 0):
            fail(f"{context}: invalid source_register_row")

        packaged_by_path: dict[str, dict[str, Any]] = {}
        for j, packaged in enumerate(row["packaged_files"]):
            pcontext = f"{context}.packaged_files[{j}]"
            path = packaged["path"]
            if path in packaged_by_path:
                prior = packaged_by_path[path]
                if prior != packaged:
                    fail(f"{pcontext}: ambiguous duplicate active locator {path!r}")
                fail(f"{pcontext}: duplicate active locator {path!r}")
            packaged_by_path[path] = packaged
            verify_bytes(skill_root, packaged, pcontext)
            packaged_total += 1
            unique_active_paths[path] = (packaged["sha256"], pcontext)

        redaction = row.get("capture_redaction")
        if redaction is not None:
            if not isinstance(redaction, dict) or not HEX256.fullmatch(str(redaction.get("original_capture_sha256", ""))):
                fail(f"{context}: malformed capture_redaction original digest provenance")
            current_path = redaction.get("current_path")
            matches = [item for item in row["packaged_files"] if item["path"] == current_path]
            if len(matches) != 1:
                fail(f"{context}: capture_redaction current_path must resolve to exactly one packaged_files locator")
            current = matches[0]
            if redaction.get("current_sha256") != current["sha256"] or redaction.get("current_bytes") != current["bytes"]:
                fail(f"{context}: capture_redaction current digest/bytes differ from packaged locator")
            if current["sha256"] == redaction["original_capture_sha256"]:
                fail(f"{context}: capture_redaction must retain a distinct original capture digest and current publishable digest")

        metadata_path, metadata_bytes = safe_file(skill_root, row["metadata_resource"], f"{context}.metadata_resource")
        try:
            metadata = json.loads(metadata_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            fail(f"{context}: metadata_resource is not valid JSON: {exc}")
        if not isinstance(metadata, dict):
            fail(f"{context}: metadata_resource must contain an object")
        if source_row is not None and metadata.get("source_register_row") != source_row:
            fail(f"{context}: metadata source_register_row does not match register row")
        if metadata.get("packaged_files") != row["packaged_files"]:
            fail(f"{context}: metadata_resource packaged_files differs from authoritative register locator")

        chunks = flatten_chunks(skill_root, row, context)
        if not chunks:
            fail(f"{context}: at least one disclosure chunk is required")
        sequences_by_source: dict[str, list[int]] = {}
        source_text_by_path: dict[str, str] = {}
        source_cursors: dict[str, int] = {}
        seen_chunk_paths: set[str] = set()
        for j, chunk in enumerate(chunks):
            ccontext = f"{context}.disclosure_chunks[{j}]"
            if not isinstance(chunk, dict):
                fail(f"{ccontext}: chunk must be an object")
            verify_bytes(skill_root, chunk, ccontext)
            source_path = chunk.get("original_text_path")
            if source_path not in packaged_by_path:
                fail(f"{ccontext}: dangling text source locator {source_path!r}; it must name exactly one packaged_files path")
            if chunk.get("text_sha256") != packaged_by_path[source_path]["sha256"]:
                fail(f"{ccontext}: text_sha256 does not match packaged source")
            if source_path not in source_text_by_path:
                source_data = (skill_root / source_path).read_bytes()
                try:
                    source_text_by_path[source_path] = source_data.decode("utf-8")
                except UnicodeDecodeError as exc:
                    fail(f"{ccontext}: declared packaged text source is not UTF-8: {exc}")
                source_cursors[source_path] = 0
            body = disclosure_body((skill_root / chunk["path"]).read_bytes(), ccontext)
            source_cursors[source_path] = validate_chunk_source_relationship(
                source_text_by_path[source_path], body, source_cursors[source_path], ccontext
            )
            sequence = chunk.get("sequence")
            if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
                fail(f"{ccontext}: invalid sequence")
            sequences_by_source.setdefault(source_path, []).append(sequence)
            path = chunk["path"]
            if path in seen_chunk_paths:
                fail(f"{ccontext}: duplicate active chunk locator {path!r}")
            seen_chunk_paths.add(path)
            chunks_total += 1
        for source_path, sequences in sequences_by_source.items():
            if sorted(sequences) != list(range(1, len(sequences) + 1)):
                fail(f"{context}: disclosure chunk sequences for {source_path!r} must be contiguous from 1")
        if metadata.get("disclosure_chunks") != row["disclosure_chunks"]:
            fail(f"{context}: metadata_resource disclosure_chunks differs from authoritative register locator")
        if metadata.get("capture_redaction") != redaction:
            if redaction is not None or metadata.get("capture_redaction") is not None:
                fail(f"{context}: metadata_resource capture_redaction differs from register provenance")

        classes[row["source_class"]] += 1
        # These overlapping tags preserve the distinction between source content, authored work,
        # explicit access gaps, navigational links, and admission status without rewriting records.
        status = row.get("download_status")
        availability = row.get("availability")
        title = str(row.get("title", "")).lower()
        source_url = row.get("source_url") or row.get("landing_page_url") or row.get("source_page_url")
        explicit_gap = any(bool(row.get(k)) for k in ("source_gap", "remaining_original_source_access_gap", "source_gap_note"))
        explicit_gap = explicit_gap or status in ("missing", "source_gap", "unavailable")
        note = str(row.get("classification_note", "")).lower()
        explicit_gap = explicit_gap or any(phrase in note for phrase in ("no static", "no copied", "not found at the named source"))
        authored = status == "authored_original" or "author-neutral" in title or "author neutral" in title
        captured = status in ("downloaded", "already_downloaded_from_source_register") or availability in (
            "downloaded_pending_content_review",
            "captured_original_or_explicit_official_alternative",
            "supplemental_official_publication_or_form_downloaded",
            "copied_bounded_guidance_or_explicit_public_alternative",
        ) or bool(source_url and row.get("original_file") and status != "authored_original")
        link_only = row.get("link_only") is True or row.get("record_type") == "link" or availability == "link_only"
        tags = set(row.get("record_kinds", []))
        tags.update(kind for kind, condition in (("authored", authored), ("source-gap", explicit_gap), ("captured", captured), ("link", link_only)) if condition)
        if str(row.get("admission_state", "")).startswith("candidate"):
            tags.add("candidate")
        invalid_tags = tags - {"captured", "authored", "source-gap", "link", "candidate"}
        if invalid_tags:
            fail(f"{context}: unknown record kind {sorted(invalid_tags)}")
        for tag in tags:
            record_kinds[tag] += 1

    return {
        "register": register_path.name,
        "rows": len(register["items"]),
        "packaged_file_locators": packaged_total,
        "disclosure_chunks": chunks_total,
        "source_classes": dict(sorted(classes.items())),
        "derived_record_tags": dict(sorted(record_kinds.items())),
    }


def validate(skill_root: Path, knowledge_rows: list[dict[str, Any]] | None = None, template_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    refdir = skill_root / "references" / "reference-register"
    schema_path = refdir / "reference-register.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    results = []
    active_locator_roles: dict[str, tuple[str, str]] = {}
    metadata_locators: set[str] = set()
    for filename, replacement_rows in zip(REGISTER_FILES, (knowledge_rows, template_rows)):
        register_path = refdir / filename
        if replacement_rows is None:
            results.append(validate_one_register(skill_root, register_path, schema))
            register = json.loads(register_path.read_text(encoding="utf-8"))
        else:
            register = json.loads(register_path.read_text(encoding="utf-8"))
            register["items"] = replacement_rows
            # Validate mutated in-memory fixtures; negative tests never write source records.
            results.append(validate_one_register(skill_root, register_path, schema, register))
        for index, row in enumerate(register["items"]):
            context = f"{filename}[{index}]"
            metadata_path = row["metadata_resource"]
            if metadata_path in metadata_locators:
                fail(f"{context}: ambiguous duplicate metadata_resource locator {metadata_path!r}")
            metadata_locators.add(metadata_path)
            locators: list[tuple[str, str, str]] = [(f["path"], "packaged_file", f["sha256"]) for f in row["packaged_files"]]
            for chunk in flatten_chunks(skill_root, row, context):
                locators.append((chunk["path"], "disclosure_chunk", chunk["sha256"]))
            for path, role, digest in locators:
                previous = active_locator_roles.get(path)
                if previous and previous != (role, digest):
                    fail(f"{context}: ambiguous active locator {path!r} conflicts with {previous[0]} or a different digest")
                active_locator_roles[path] = (role, digest)
    collision = set(metadata_locators) & set(active_locator_roles)
    if collision:
        fail(f"metadata_resource path collides with active content locator {sorted(collision)[0]!r}")
    totals = {
        "registers": results,
        "rows": sum(r["rows"] for r in results),
        "packaged_file_locators": sum(r["packaged_file_locators"] for r in results),
        "disclosure_chunks": sum(r["disclosure_chunks"] for r in results),
        "unique_active_content_paths": len(active_locator_roles),
        "metadata_resources": len(metadata_locators),
    }
    expected_rows = {"knowledge-register.json": 145, "template-register.json": 105}
    for result in results:
        if result["rows"] != expected_rows[result["register"]]:
            fail(f"{result['register']}: expected {expected_rows[result['register']]} records, found {result['rows']}")
    return totals


def self_test(skill_root: Path) -> dict[str, Any]:
    knowledge = json.loads((skill_root / "references/reference-register/knowledge-register.json").read_text(encoding="utf-8"))["items"]
    template = json.loads((skill_root / "references/reference-register/template-register.json").read_text(encoding="utf-8"))["items"]
    cases: list[tuple[str, list[dict[str, Any]], list[dict[str, Any]], str]] = []

    def add(name: str, krows: list[dict[str, Any]], trows: list[dict[str, Any]], expected: str) -> None:
        cases.append((name, krows, trows, expected))

    mutate = copy.deepcopy(knowledge)
    mutate[0]["packaged_files"][0]["sha256"] = "0" * 64
    add("packaged_hash_mismatch", mutate, copy.deepcopy(template), "sha256 mismatch")

    mutate = copy.deepcopy(template)
    mutate[0]["packaged_files"][0]["bytes"] += 1
    add("packaged_byte_count_mismatch", copy.deepcopy(knowledge), mutate, "byte-count mismatch")

    mutate = copy.deepcopy(knowledge)
    mutate[0]["packaged_files"][0]["path"] = "references/reference-register/assets/does-not-exist.bin"
    add("missing_packaged_locator", mutate, copy.deepcopy(template), "missing or out-of-root path")

    mutate = copy.deepcopy(template)
    mutate[0]["disclosure_chunks"][0]["original_text_path"] = "references/reference-register/assets/unlisted-source.txt"
    add("dangling_chunk_source", copy.deepcopy(knowledge), mutate, "dangling text source locator")

    altered_wrapper = b"# Test chunk\n\nSource/reference only; bounded test.\n\nomitted words\n"
    try:
        validate_chunk_source_relationship("alpha beta\n", disclosure_body(altered_wrapper, "negative-chunk"), 0, "negative-chunk")
    except ValueError as exc:
        body_negative = {"case": "chunk_body_not_from_source", "expected_rejection": "not an ordered substring", "passed": "not an ordered substring" in str(exc), "observed": str(exc)}
    else:
        body_negative = {"case": "chunk_body_not_from_source", "expected_rejection": "not an ordered substring", "passed": False, "observed": "unexpected acceptance"}

    mutate = copy.deepcopy(template)
    mutate[0]["packaged_files"].append(copy.deepcopy(mutate[0]["packaged_files"][0]))
    mutate[0]["packaged_files"][-1]["sha256"] = "1" * 64
    add("ambiguous_duplicate_active_locator", copy.deepcopy(knowledge), mutate, "ambiguous duplicate active locator")

    mutate = copy.deepcopy(knowledge)
    mutate[0]["resource_class"] = "template"
    add("wrong_resource_class", mutate, copy.deepcopy(template), "schema error")

    mutate = copy.deepcopy(knowledge)
    mutate[0]["record_kinds"] = ["unrecognized"]
    add("unknown_record_kind", mutate, copy.deepcopy(template), "schema error")

    mutate = copy.deepcopy(knowledge)
    mutate[5]["capture_redaction"]["current_bytes"] += 1
    add("redaction_locator_mismatch", mutate, copy.deepcopy(template), "capture_redaction current digest/bytes differ")

    results = []
    for name, krows, trows, expected in cases:
        try:
            validate(skill_root, krows, trows)
        except ValueError as exc:
            message = str(exc)
            passed = expected in message
        else:
            message = "unexpected acceptance"
            passed = False
        results.append({"case": name, "expected_rejection": expected, "passed": passed, "observed": message[:500]})
    results.append(body_negative)
    return {"negative_cases": results, "passed": all(item["passed"] for item in results)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        positive = validate(args.skill_root)
        negative = self_test(args.skill_root) if args.self_test else None
        if negative and not negative["passed"]:
            raise ValueError("one or more controlled negative cases were accepted or failed for the wrong reason")
        refdir = args.skill_root / "references" / "reference-register"
        result = {
            "status": "PASS",
            "validated_at_utc": datetime.now(timezone.utc).isoformat(),
            "positive_validation": positive,
            "controlled_negative_tests": negative,
            "input_sha256": {
                filename: hashlib.sha256((refdir / filename).read_bytes()).hexdigest()
                for filename in REGISTER_FILES
            },
            "schema_sha256": hashlib.sha256((refdir / "reference-register.schema.json").read_bytes()).hexdigest(),
        }
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
