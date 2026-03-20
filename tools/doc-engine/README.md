# doc-engine

## Capability Summary
Document processing engine with OCR extraction (`unstructured`), format conversion (`pandoc`), and Markdown-to-Google-Doc printing for venture workflows.

## Commands
- `ocr`
  - Run OCR/text extraction on a file using `unstructured`.
- `convert`
  - Convert files using `pandoc` between explicit formats.
- `print-to-google-doc`
  - Create a Google Doc from Markdown text and append formatted Markdown content.

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/doc-engine ocr --file-path ./scanned-contract.pdf`
- `bin/doc-engine convert --input-path ./draft.md --output-path ./draft.html --from-format markdown --to-format html`
- `bin/doc-engine print-to-google-doc --title "Ops Brief" --markdown-file ./brief.md`

## Dependencies
- `unstructured`
- `pandoc` executable available on PATH
- `gws` configured for Workspace Docs operations (plus Vault credentials as needed)
