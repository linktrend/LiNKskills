# Meeting-management interface

The consumer supplies a synthetic or redacted meeting request with a meeting
reference, purpose, participants, agenda inputs, notes/transcript reference,
decisions, commitments, task destinations, evidence, and authority. The output
contains agenda/pre-brief/notes, evidence-bound decisions and follow-ups,
reference-only routing, maintained-candidate review, privacy assertions, and an
empty effects envelope.

Raw transcript text, live participant identity, credentials, private account
data, and destination payloads are rejected or omitted. The helper never opens
Google, Brain, Program, Calendar, agent, or messaging stores and never sends or
creates a meeting artifact.
