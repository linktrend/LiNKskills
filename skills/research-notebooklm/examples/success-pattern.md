# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "action": "query_existing_notebook",
  "notebook_identity": "FIC-NB-01",
  "source_question": "Summarize source A claim about metric Y.",
  "output_type": "answer",
  "existing_session_capability": "visible session assumed only for illustration",
  "write_authorization": "read-only",
  "as_of": "2026-10-05"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "needs_input",
    "operation": "query_existing_notebook",
    "notebook_identity": "FIC-NB-01",
    "visible_session_evidence": "No actual UI was accessed; fictional example only.",
    "source_attributions": [
      {
        "source_label": "FIC-SOURCE-A",
        "citation_location": "page 2",
        "claim": "synthetic placeholder claim"
      }
    ],
    "answer": "A real answer requires an accessible authorized NotebookLM session and source content.",
    "write_action": {
      "requested": false,
      "performed": false,
      "confirmation": "none"
    },
    "generated_output": {
      "type": "not generated",
      "prompt_parameters": null,
      "completion_state": "not started"
    },
    "limitations": [
      "No notebook operation or UI success is claimed."
    ]
  }
}
```
