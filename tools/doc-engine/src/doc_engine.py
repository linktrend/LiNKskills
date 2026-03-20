from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


class DocEngineService:
    """Document processing engine with OCR, conversion, and Google Doc printing."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root).expanduser().resolve() if repo_root else Path(__file__).resolve().parents[3]
        self.gws_cli_path = self.repo_root / "tools" / "gws" / "bin" / "gws"

    def ocr_extract(self, file_path: str | Path) -> dict[str, Any]:
        path = Path(file_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")

        try:
            from unstructured.partition.auto import partition
        except Exception as exc:
            raise RuntimeError(
                "unstructured is required for OCR extraction. Install dependencies first."
            ) from exc

        elements = partition(filename=str(path))
        text_parts: list[str] = []
        for element in elements:
            value = getattr(element, "text", None)
            if value is None:
                value = str(element)
            if value:
                text_parts.append(str(value).strip())

        text = "\n".join([part for part in text_parts if part]).strip()
        return {
            "status": "success",
            "source": str(path),
            "chars": len(text),
            "text": text,
        }

    def convert_with_pandoc(
        self,
        input_path: str | Path,
        output_path: str | Path,
        from_format: str,
        to_format: str,
    ) -> dict[str, Any]:
        source = Path(input_path).expanduser().resolve()
        target = Path(output_path).expanduser().resolve()
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(f"Input file not found: {source}")

        target.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "pandoc",
            str(source),
            "-f",
            from_format,
            "-t",
            to_format,
            "-o",
            str(target),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "pandoc conversion failed")

        return {
            "status": "success",
            "input": str(source),
            "output": str(target),
            "from": from_format,
            "to": to_format,
        }

    def print_to_google_doc(self, markdown_text: str, title: str) -> dict[str, Any]:
        if not self.gws_cli_path.exists():
            raise FileNotFoundError(f"gws CLI not found at {self.gws_cli_path}")
        if not markdown_text.strip():
            raise ValueError("markdown_text must be non-empty")

        create_payload = self._run_gws_json([
            str(self.gws_cli_path),
            "docs",
            "documents",
            "create",
            "--json",
            json.dumps({"title": title}),
        ])

        document_id = (
            create_payload.get("documentId")
            or create_payload.get("id")
            or create_payload.get("document_id")
        )
        if not isinstance(document_id, str) or not document_id:
            raise RuntimeError("Google Doc create response missing document_id")

        append_payload = self._run_gws_json([
            str(self.gws_cli_path),
            "docs",
            "+write",
            "--document-id",
            document_id,
            "--text",
            markdown_text,
        ])

        return {
            "status": "success",
            "document_id": document_id,
            "title": title,
            "appended_chars": len(markdown_text),
            "write_result": append_payload,
        }

    def _run_gws_json(self, command: list[str]) -> dict[str, Any]:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        stdout = completed.stdout.strip()
        if not stdout:
            raise RuntimeError(completed.stderr.strip() or "gws command returned no output")

        try:
            payload = json.loads(stdout.splitlines()[-1])
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Unable to parse gws JSON output: {stdout}") from exc

        if completed.returncode != 0 and not payload:
            raise RuntimeError(completed.stderr.strip() or "gws command failed")
        return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LiNKskills Document Engine CLI")
    parser.add_argument("--version", action="version", version="doc-engine 1.0.0")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    ocr_parser = subparsers.add_parser("ocr", help="Extract text with OCR and structure analysis")
    ocr_parser.add_argument("--file-path", required=True, type=str)

    convert_parser = subparsers.add_parser("convert", help="Convert document formats with pandoc")
    convert_parser.add_argument("--input-path", required=True, type=str)
    convert_parser.add_argument("--output-path", required=True, type=str)
    convert_parser.add_argument("--from-format", required=True, type=str)
    convert_parser.add_argument("--to-format", required=True, type=str)

    print_parser = subparsers.add_parser(
        "print-to-google-doc",
        help="Create a Google Doc from Markdown text",
    )
    print_parser.add_argument("--title", required=True, type=str)
    print_parser.add_argument("--markdown-text", default=None, type=str)
    print_parser.add_argument("--markdown-file", default=None, type=str)

    return parser


def _resolve_markdown(markdown_text: str | None, markdown_file: str | None) -> str:
    if markdown_text and markdown_text.strip():
        return markdown_text
    if markdown_file:
        path = Path(markdown_file).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Markdown file not found: {path}")
        return path.read_text(encoding="utf-8")
    raise ValueError("Provide --markdown-text or --markdown-file")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        service = DocEngineService()
        if args.command == "ocr":
            result = service.ocr_extract(file_path=args.file_path)
        elif args.command == "convert":
            result = service.convert_with_pandoc(
                input_path=args.input_path,
                output_path=args.output_path,
                from_format=args.from_format,
                to_format=args.to_format,
            )
        elif args.command == "print-to-google-doc":
            markdown = _resolve_markdown(args.markdown_text, args.markdown_file)
            result = service.print_to_google_doc(markdown_text=markdown, title=args.title)
        else:
            raise ValueError(f"Unsupported command: {args.command}")

        print(
            json.dumps(
                {"status": "success", "output": result, "path": "doc-engine"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "output": str(exc), "path": "doc-engine"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
