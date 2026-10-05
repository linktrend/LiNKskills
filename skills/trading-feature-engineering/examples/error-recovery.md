# Error and gap handling

Return `needs_input` when missing information changes the analysis method. Return `partial` when a bounded subset remains interpretable and list unresolved fields. Return `blocked` only when identity, authority, or source validity prevents safe analysis. Do not fill missing values or infer owner limits.
