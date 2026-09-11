-- migrate:down
-- Exact-object rollback for 20260910_000013_lskills_production_store_readiness.sql.
-- Removes only the binder table, policies, and snapshot function.
-- Does not drop schema lskills, prior tables, or Platform LOGIN roles.
-- LiNKplatform alone decides whether this down file is applied.

drop function if exists lskills.store_readiness_snapshot();
drop policy if exists lskills_store_package_runtime_select on lskills.store_package;
drop policy if exists lskills_store_package_observer_select on lskills.store_package;
drop table if exists lskills.store_package;
