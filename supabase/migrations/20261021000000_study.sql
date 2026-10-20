-- Study progress (web/study.js) syncs like the rest of My atlas: one atlas_items row per review card
-- (item_id "c:<card key>"), plus "done" (lessons read) and "stats". Only the allowed kinds change.
alter table public.atlas_items drop constraint if exists atlas_items_kind_check;
alter table public.atlas_items add constraint atlas_items_kind_check
  check (kind in ('saved', 'tasting', 'note', 'state', 'study'));
