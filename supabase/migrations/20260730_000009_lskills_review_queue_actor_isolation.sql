-- migrate:up
-- LiNKskills Librarian review_queue actor+org isolation — additive upgrade
--
-- ADDITIVE ONLY. Does NOT rewrite 20260730_000008_lskills_review_queue.sql.
-- Tightens RLS on lskills.review_queue so default visibility requires BOTH
-- organization AND actor match. Same-org wrong-actor is DENIED unless an
-- explicit privileged Librarian service scope GUC is set for the transaction.
--
-- Privileged cross-actor (within org) — Librarian service workers only:
--   SET LOCAL ROLE svc_lskills_librarian;
--   select set_config('app.current_org_id', '<org>', true);
--   select set_config('app.current_actor_id', '<actor>', true);  -- still required
--   select set_config('app.librarian_service_scope', 'org', true);
-- When app.librarian_service_scope = 'org', svc_lskills_librarian may see/claim
-- rows for any actor in the bound org. Absent/empty scope keeps actor isolation.
-- Runtime (svc_lskills_runtime) remains actor+org only — no privileged GUC path.
-- Observer remains org-scoped read for approved monitoring (unchanged from 000008).
--
-- IMPORTANT: LiNKplatform alone applies live shared migrations.
-- This file is authored in LiNKskills for review/handoff; do not apply
-- from a Skills agent session to stage/prod.
--
-- Prerequisite: 20260730_000008_lskills_review_queue.sql
--   (table + roles + org_matches / actor_matches helpers).

-- ---------------------------------------------------------------------------
-- Visibility helper — default actor+org; optional librarian org service scope
-- ---------------------------------------------------------------------------
create or replace function lskills.review_queue_librarian_visible(
  row_org_id text,
  row_actor_id text
)
returns boolean
language sql
stable
as $$
  select lskills.org_matches(row_org_id)
    and (
      lskills.actor_matches(row_actor_id)
      or nullif(current_setting('app.librarian_service_scope', true), '') = 'org'
    );
$$;

grant execute on function lskills.review_queue_librarian_visible(text, text)
  to svc_lskills_runtime, svc_lskills_librarian, svc_observer;

-- ---------------------------------------------------------------------------
-- Replace librarian policy: actor+org default; org-wide only when GUC gated
-- ---------------------------------------------------------------------------
drop policy if exists lskills_review_queue_librarian_all on lskills.review_queue;
create policy lskills_review_queue_librarian_all on lskills.review_queue
  for all to svc_lskills_librarian
  using (lskills.review_queue_librarian_visible(org_id, actor_id))
  with check (lskills.review_queue_librarian_visible(org_id, actor_id));

-- Runtime policies already require actor+org in 000008; recreate for clarity
-- and to ensure upgrade DBs keep the same fail-closed contract.
drop policy if exists lskills_review_queue_runtime_insert on lskills.review_queue;
create policy lskills_review_queue_runtime_insert on lskills.review_queue
  for insert to svc_lskills_runtime
  with check (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

drop policy if exists lskills_review_queue_runtime_select on lskills.review_queue;
create policy lskills_review_queue_runtime_select on lskills.review_queue
  for select to svc_lskills_runtime
  using (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

-- Observer: org-scoped monitoring read (explicit; not actor-isolated).
-- Cross-actor claim/write remains librarian-only via service scope GUC.
drop policy if exists lskills_review_queue_observer_read on lskills.review_queue;
create policy lskills_review_queue_observer_read on lskills.review_queue
  for select to svc_observer
  using (lskills.org_matches(org_id));

-- verification helpers (safe SELECT-only)
select
  p.polname as policy_name,
  pg_get_expr(p.polqual, p.polrelid) as using_expr
from pg_policy p
join pg_class c on c.oid = p.polrelid
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'lskills'
  and c.relname = 'review_queue'
order by p.polname;

-- ---------------------------------------------------------------------------
-- DOWN-MIGRATION: intentionally NOT in this file.
-- If needed, create a separately dated *_down.sql that restores the 000008
-- librarian org-only policy and drops review_queue_librarian_visible —
-- never drop lskills.review_queue or the lskills schema.
-- ---------------------------------------------------------------------------
