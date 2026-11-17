-- Wine Passport: a public profile a member can choose to show, tasting notes a member can choose to share, and the
-- reports and moderation that come with public content.
--
-- Nothing becomes public by itself. A profile is private until its owner turns it public, and a tasting note is shared
-- only when its owner marks it public AND the profile is public. Tasting notes stay where they already live
-- (atlas_items, kind "tasting", synced from My atlas); the public functions below read them with every filter applied.
-- The place a note was tasted at is a venue name and a town (GeoNames), never a precise position.
--
-- Moderation lives in tables only the admin functions touch, so a member cannot undo it by editing their own rows.

-- ---------- profile: a handle for the Passport address, the public switch, and when onboarding was answered
alter table public.profiles add column if not exists handle text;
alter table public.profiles add column if not exists is_public boolean not null default false;
alter table public.profiles add column if not exists onboarded_at timestamptz;
alter table public.profiles drop constraint if exists profiles_handle_format;
alter table public.profiles add constraint profiles_handle_format
  check (handle is null or handle ~ '^[a-z0-9][a-z0-9_-]{2,29}$');
create unique index if not exists profiles_handle_key on public.profiles (lower(handle));
-- a public profile needs a handle
alter table public.profiles drop constraint if exists profiles_public_needs_handle;
alter table public.profiles add constraint profiles_public_needs_handle check (not is_public or handle is not null);
-- handles that would look official or collide with pages of the site
create or replace function public.profiles_check_handle()
returns trigger language plpgsql set search_path = '' as $$
begin
  if new.handle is not null then
    new.handle := lower(new.handle);
    if new.handle in ('admin', 'administrator', 'openwineatlas', 'open-wine-atlas', 'owa', 'atlas', 'support', 'help',
                      'founding', 'founder', 'moderator', 'mod', 'staff', 'team', 'official', 'root', 'null', 'undefined',
                      'about', 'terms', 'privacy', 'legal', 'places', 'study', 'u', 'api', 'www', 'mail', 'hello')
       or new.handle like 'openwineatlas%' then
      raise exception 'handle not allowed' using errcode = '23514';
    end if;
  end if;
  return new;
end $$;
drop trigger if exists profiles_handle on public.profiles;
create trigger profiles_handle before insert or update of handle on public.profiles
  for each row execute function public.profiles_check_handle();

-- shared tasting notes are looked up by place
create index if not exists atlas_items_public_tasting_place on public.atlas_items ((data ->> 'placeId'))
  where kind = 'tasting' and not deleted and (data ->> 'public') = 'true';

-- ---------- moderation (admin only)
create table if not exists public.moderation_blocks (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  reason     text check (char_length(reason) <= 500),
  created_at timestamptz not null default now()
);
create table if not exists public.moderation_hidden (
  user_id    uuid not null references auth.users (id) on delete cascade,
  item_id    text not null,
  reason     text check (char_length(reason) <= 500),
  created_at timestamptz not null default now(),
  primary key (user_id, item_id)
);
create table if not exists public.reports (
  id          uuid primary key default gen_random_uuid(),
  kind        text not null check (kind in ('tasting', 'profile')),
  target_user uuid not null references auth.users (id) on delete cascade,
  target_item text check (char_length(target_item) <= 120),
  reason      text check (char_length(reason) <= 500),
  reporter    uuid references auth.users (id) on delete set null,
  status      text not null default 'open' check (status in ('open', 'hidden', 'dismissed')),
  created_at  timestamptz not null default now()
);
create index if not exists reports_open on public.reports (created_at) where status = 'open';
alter table public.moderation_blocks enable row level security;
alter table public.moderation_hidden enable row level security;
alter table public.reports enable row level security;
revoke all on public.moderation_blocks, public.moderation_hidden, public.reports from anon, authenticated;

-- ---------- reading: what a visitor may see
-- a shared tasting note as the public sees it; the town only, never more
create or replace function public.public_tasting_json(i public.atlas_items, p public.profiles)
returns jsonb language sql stable set search_path = '' as $$
  select jsonb_strip_nulls(jsonb_build_object(
    'id', i.item_id,
    'handle', p.handle,
    'name', p.display_name,
    'place_id', left(i.data ->> 'placeId', 120),
    'place', left(i.data ->> 'place', 140),
    'country', left(i.data ->> 'country', 4),
    'wine', left(i.data ->> 'wine', 140),
    'vintage', case when (i.data ->> 'vintage') ~ '^\d{4}$' then (i.data ->> 'vintage')::int end,
    'score', case when (i.data ->> 'score') ~ '^\d{2,3}$' and (i.data ->> 'score')::int between 50 and 100 then (i.data ->> 'score')::int end,
    'date', case when (i.data ->> 'date') ~ '^\d{4}-\d{2}-\d{2}$' then i.data ->> 'date' end,
    'note', left(i.data ->> 'note', 3000),
    'venue', left(i.data #>> '{tastedAt,venue}', 80),
    'city', left(i.data #>> '{tastedAt,city}', 80),
    'city_cc', left(i.data #>> '{tastedAt,cc}', 2),
    'city_lat', case when (i.data #>> '{tastedAt,lat}') ~ '^-?\d{1,2}(\.\d+)?$' then round((i.data #>> '{tastedAt,lat}')::numeric, 2) end,
    'city_lon', case when (i.data #>> '{tastedAt,lon}') ~ '^-?\d{1,3}(\.\d+)?$' then round((i.data #>> '{tastedAt,lon}')::numeric, 2) end,
    'lat', case when (i.data ->> 'lat') ~ '^-?\d{1,2}(\.\d+)?$' then round((i.data ->> 'lat')::numeric, 3) end,
    'lon', case when (i.data ->> 'lon') ~ '^-?\d{1,3}(\.\d+)?$' then round((i.data ->> 'lon')::numeric, 3) end
  ));
$$;

-- the Passport of a public member, by handle: profile, Founding badge, shared notes and study progress
create or replace function public.passport(p_handle text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare p public.profiles; out jsonb; spot integer;
begin
  select * into p from public.profiles where lower(handle) = lower(p_handle) and is_public;
  if not found or exists (select 1 from public.moderation_blocks b where b.user_id = p.id) then return null; end if;
  select r.rank into spot from (
    select (select count(*)::integer from public.founding_waitlist c where c.status = 'confirmed' and c.position <= w.position) as rank
      from public.founding_waitlist w join auth.users u on lower(u.email) = lower(w.email::text)
     where u.id = p.id and w.status = 'confirmed') r;
  select jsonb_build_object(
    'handle', p.handle, 'name', p.display_name, 'level', p.level, 'studying', p.studying, 'location', p.location,
    'bio', p.bio, 'favourites', to_jsonb(p.favourite_places), 'since', p.created_at::date,
    'founding', case when spot is not null and spot <= 1000 then spot end,
    'tastings', coalesce((select jsonb_agg(public.public_tasting_json(i, p) order by i.data ->> 'date' desc nulls last, i.updated_at desc)
        from public.atlas_items i
       where i.user_id = p.id and i.kind = 'tasting' and not i.deleted and (i.data ->> 'public') = 'true'
         and not exists (select 1 from public.moderation_hidden h where h.user_id = i.user_id and h.item_id = i.item_id)), '[]'::jsonb),
    'lessons', coalesce((select jsonb_path_query_array(i.data -> 'v', 'strict $.keyvalue().key')
        from public.atlas_items i where i.user_id = p.id and i.kind = 'study' and i.item_id = 'done' and not i.deleted), '[]'::jsonb)
  ) into out;
  return out;
end $$;

-- shared notes on one place, newest first
create or replace function public.place_tastings(p_place text, p_limit integer default 20)
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(t.j order by t.d desc nulls last, t.u desc), '[]'::jsonb) from (
    select public.public_tasting_json(i, p) as j, i.data ->> 'date' as d, i.updated_at as u
      from public.atlas_items i join public.profiles p on p.id = i.user_id
     where (i.data ->> 'placeId') = p_place and i.kind = 'tasting' and not i.deleted and (i.data ->> 'public') = 'true'
       and p.is_public
       and not exists (select 1 from public.moderation_blocks b where b.user_id = i.user_id)
       and not exists (select 1 from public.moderation_hidden h where h.user_id = i.user_id and h.item_id = i.item_id)
     order by i.updated_at desc
     limit least(greatest(coalesce(p_limit, 20), 1), 50)) t;
$$;

-- is this handle free? (for the form, before saving)
create or replace function public.handle_free(p_handle text)
returns boolean language sql stable security definer set search_path = '' as $$
  select p_handle ~ '^[a-z0-9][a-z0-9_-]{2,29}$'
     and not exists (select 1 from public.profiles where lower(handle) = lower(p_handle) and id is distinct from auth.uid());
$$;

-- ---------- reporting: anyone may report public content, a few times per target
create or replace function public.report_content(p_kind text, p_handle text, p_item text, p_reason text)
returns void language plpgsql security definer set search_path = '' as $$
declare uid uuid;
begin
  if p_kind not in ('tasting', 'profile') then raise exception 'bad kind' using errcode = '22023'; end if;
  select id into uid from public.profiles where lower(handle) = lower(p_handle) and is_public;
  if uid is null then return; end if;
  if (select count(*) from public.reports r where r.target_user = uid and r.target_item is not distinct from p_item and r.status = 'open') >= 20 then return; end if;
  if (select count(*) from public.reports r where r.created_at > now() - interval '1 hour') >= 200 then return; end if;
  insert into public.reports (kind, target_user, target_item, reason, reporter)
  values (p_kind, uid, case when p_kind = 'tasting' then left(p_item, 120) end, left(nullif(trim(p_reason), ''), 500), auth.uid());
end $$;

-- ---------- admin: reports and the two moderation actions
create or replace function public.admin_reports()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.is_admin() then raise exception 'not allowed' using errcode = '42501'; end if;
  return coalesce((select jsonb_agg(jsonb_build_object(
      'kind', g.kind, 'handle', p.handle, 'name', p.display_name, 'item', g.target_item,
      'count', g.n, 'last', g.last, 'reasons', g.reasons,
      'content', case when g.kind = 'tasting' then (select public.public_tasting_json(i, p) from public.atlas_items i
                   where i.user_id = g.target_user and i.kind = 'tasting' and i.item_id = g.target_item)
                 else jsonb_build_object('bio', p.bio, 'location', p.location) end,
      'hidden', exists (select 1 from public.moderation_hidden h where h.user_id = g.target_user and h.item_id = g.target_item),
      'blocked', exists (select 1 from public.moderation_blocks b where b.user_id = g.target_user)) order by g.last desc)
    from (select r.kind, r.target_user, r.target_item, count(*) as n, max(r.created_at) as last,
                 coalesce(jsonb_agg(r.reason) filter (where r.reason is not null), '[]'::jsonb) as reasons
            from public.reports r where r.status = 'open' group by r.kind, r.target_user, r.target_item) g
    join public.profiles p on p.id = g.target_user), '[]'::jsonb);
end $$;

-- hide one note, or block a member's whole public presence; both close the open reports on it
create or replace function public.admin_moderate(p_action text, p_handle text, p_item text default null, p_reason text default null)
returns void language plpgsql security definer set search_path = '' as $$
declare uid uuid;
begin
  if not public.is_admin() then raise exception 'not allowed' using errcode = '42501'; end if;
  select id into uid from public.profiles where lower(handle) = lower(p_handle);
  if uid is null then raise exception 'no such member' using errcode = 'P0002'; end if;
  if p_action = 'hide' then
    insert into public.moderation_hidden (user_id, item_id, reason) values (uid, p_item, p_reason) on conflict do nothing;
    update public.reports set status = 'hidden' where target_user = uid and target_item = p_item and status = 'open';
  elsif p_action = 'unhide' then
    delete from public.moderation_hidden where user_id = uid and item_id = p_item;
  elsif p_action = 'block' then
    insert into public.moderation_blocks (user_id, reason) values (uid, p_reason) on conflict (user_id) do update set reason = excluded.reason;
    update public.reports set status = 'hidden' where target_user = uid and status = 'open';
  elsif p_action = 'unblock' then
    delete from public.moderation_blocks where user_id = uid;
  elsif p_action = 'dismiss' then
    update public.reports set status = 'dismissed' where target_user = uid and target_item is not distinct from p_item and status = 'open';
  else
    raise exception 'bad action' using errcode = '22023';
  end if;
end $$;

revoke all on function public.public_tasting_json(public.atlas_items, public.profiles), public.passport(text), public.place_tastings(text, integer),
  public.handle_free(text), public.report_content(text, text, text, text), public.admin_reports(), public.admin_moderate(text, text, text, text),
  public.profiles_check_handle() from public, anon, authenticated;
grant execute on function public.passport(text), public.place_tastings(text, integer), public.report_content(text, text, text, text) to anon, authenticated;
grant execute on function public.handle_free(text), public.admin_reports(), public.admin_moderate(text, text, text, text) to authenticated;
