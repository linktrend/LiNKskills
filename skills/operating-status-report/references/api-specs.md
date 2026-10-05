# Current consumer interfaces

Use only tools exposed in the active native catalog; these routes are not extra grants.

- `linkskills_use({operation,arguments})`: qualification and entrypoint take exact `skill_id`,`version`; list support with `skills_release_resources_list`; retrieve by exact returned content ID through `skills_release_content_get`. Never guess IDs or use latest.
- `workspace__shared_drive_create({name,kind})`: authorized draft creation in LiNKdrive, kinds doc/sheet/slide. `workspace__google_workspace({args:[...]})`: documented Drive/Docs/Sheets interface; inspect its current schema/help and read back edits. This is separate from metadata-only `workspace__shared_drive_files`.
- `sessions_send({sessionKey,message})`, `sessions_history({sessionKey,limit,offset})`, `session_status({sessionKey})`: parent Sara's exact enrolled retained specialists only. A child lacking content tools receives minimized authorized source extracts and returns work in its assigned session.
- `linkbrain__brain_append_finding`: finding/title/summary/confidence/proposedAt/evidenceRefs/idempotency; use exact current supplied schema. Candidate acceptance is not canonical promotion. Approved knowledge needs search followed by explicit load and authority/admission readback.
- Native session persistence is consumer-owned. `linkbrain_write` checkpoint calls require separate granted operation and trusted task binding; no tool availability is implied.

No source-side CLI/MCP/HRIS access is inherited. Helper validates a supplied artifact contract only, not model behavior. Upstream support scripts are copied data pending explicit inspection; never run them automatically.
