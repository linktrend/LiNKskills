# Optional structural helper

`helper_tool.py` checks only presence of required envelope keys from JSON on stdin, prints missing field names but no values, and performs no network or business-system calls. It is for offline structural checks; Sara's current runtime has no shell executor and must not call it. Native schemas and owner toolcards govern actual tool use.
