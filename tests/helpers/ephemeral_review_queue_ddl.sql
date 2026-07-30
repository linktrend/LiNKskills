-- Ephemeral-only DDL for Librarian review-queue Postgres proofs.
-- NOT a live migration. Do not apply to stage/prod.
-- LiNKplatform alone applies live shared migrations.
--
-- Used by tests when LINKSKILLS_EPHEMERAL_PG_URL / docker Postgres is available.

create schema if not exists lskills;

create table if not exists lskills.review_queue (
  review_id text primary key,
  kind text not null,
  status text not null default 'queued',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists review_queue_status_idx
  on lskills.review_queue (status);
