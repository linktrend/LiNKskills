# Method-specific extension

## Applied method

1. Confirm that the request is specifically for NotebookLM; otherwise route to general research methods.
2. Check only currently available browser UI tools and the user’s active authorized session; stop if unavailable or login is required.
3. Identify the notebook from user-supplied name or URL and disambiguate without handling credentials.
4. Before adding sources or generating content, confirm the requested destination and operation; do not silently publish or change shared notebooks.
5. Inspect the current UI for supported actions/options because product menus change; do not rely on dated Studio feature lists.
6. Perform the narrow requested operation, wait for visible completion, and verify result in the notebook.
7. Report what succeeded and what was inaccessible; never claim notebook content is independently verified by the product.

## Focused support: authorized session and asynchronous actions

Use only the existing signed-in browser session the user authorized. Navigate from the notebook identity the user supplied, verify the notebook title/owner context before acting, and stop if the page requests login, a new permission, or an ambiguous shared destination. Do not automate sign-in, capture credentials, or treat browser access as permission to add or share material.

Product controls and generation options change. Inspect the current UI for supported source, prompt, and output actions; do not follow a stale automation recipe or fixed prompt library. Before a write or generation, confirm the requested destination and input scope. After submission, wait for visible completion and inspect the resulting artifact in the same notebook. If the UI remains pending, errors, or does not show the expected output, report that exact state instead of retrying blindly or claiming success.

When summarizing notebook answers, cite the displayed source labels and distinguish notebook-grounded content from external verification. The notebook may omit or misstate its sources; it does not independently verify claims.

## Scope guard

Use only on an explicit NotebookLM request and an already authorized current browser session; do not automate login or handle credentials.

If the requested method cannot be completed with available evidence or tools, return a bounded partial deliverable and name the precise gap. Do not replace a missing input with an invented value.
