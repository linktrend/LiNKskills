# Developer validation helper

`helper_tool.py` validates a real supplied JSON input or output object against `references/schemas.json`. It uses the repository's standard-library contract validator, is read-only, and returns structural validity only. It does not create a behavioral PASS, qualify the research method, fetch data, or execute upstream code. It is not a native Jane host tool.
