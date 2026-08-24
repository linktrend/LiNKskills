-- migrate:down
-- PKT-03 source-package rollback only. LiNKplatform controls whether this is
-- ever applied. Remove only the exact additive objects created by the paired
-- migration, never vendor bytes or prior release tables.
drop table if exists lskills.external_platform_receipts;
drop table if exists lskills.external_current_pointers;
drop table if exists lskills.external_librarian_reviews;
drop table if exists lskills.external_update_candidates;
drop table if exists lskills.external_adapted_releases;
drop table if exists lskills.external_collection_manifests;
drop table if exists lskills.external_vendor_releases;
