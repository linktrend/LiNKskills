# Private health interface

The consumer supplies an opaque `subject_ref`, a private storage/backup policy,
checkpoint times, enabled health fields, and clinician boundaries. Observations
are append-only records with source and confidence. The output has two separate
parts: a private report for the approved destination and one coarse capacity
state. The redaction receipt proves that detailed fields were not emitted to
work or shared-agent channels.
