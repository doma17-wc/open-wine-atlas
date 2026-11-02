-- Last seen: when an account really used the atlas.
--
-- The admin page used auth.users.last_sign_in_at, which only moves when someone types a sign-in code. A session stays
-- open for weeks, so a person who came back every day still looked gone since their last code.
--
-- Now the map and the admin page call touch_seen() while the page is open and visible. One row per account with the
-- latest time only, deleted with the account. The daily number is a plain total in site_events, with no user in it.

create table public.account_activity (
  user_id      uuid primary key references auth.users (id) on delete cascade,
  last_seen_at timestamptz not null default now()
);
alter table public.account_activity enable row level security;
revoke all on public.account_activity from anon, authenticated;

create or replace function public.touch_seen()
returns void language plpgsql security definer set search_path = '' as $$
declare uid uuid := auth.uid(); prev timestamptz;
begin
  if uid is null then return; end if;
  select a.last_seen_at into prev from public.account_activity a where a.user_id = uid for update;
  if prev > now() - interval '1 minute' then return; end if;
  insert into public.account_activity as a (user_id, last_seen_at) values (uid, now())
  on conflict (user_id) do update set last_seen_at = excluded.last_seen_at;
  -- the first visit of the day (Zurich time) counts once
  if prev is null or (prev at time zone 'Europe/Zurich')::date < (now() at time zone 'Europe/Zurich')::date then
    insert into public.site_events as e (name, n) values ('active_accounts', 1)
    on conflict (day, name) do update set n = e.n + 1;
  end if;
end $$;

-- start from the best evidence already in the database: the last sign-in, the session and the last synced item
insert into public.account_activity (user_id, last_seen_at)
select u.id, greatest(u.last_sign_in_at, s.t, i.t)
from auth.users u
left join lateral (select max(greatest(x.refreshed_at at time zone 'UTC', x.updated_at)) t from auth.sessions x where x.user_id = u.id) s on true
left join lateral (select max(x.updated_at) t from public.atlas_items x where x.user_id = u.id) i on true
where greatest(u.last_sign_in_at, s.t, i.t) is not null;

-- accounts already seen today are not counted again by touch_seen, so they start the counter
insert into public.site_events as e (name, n)
select 'active_accounts', count(*) from public.account_activity a
where (a.last_seen_at at time zone 'Europe/Zurich')::date = (now() at time zone 'Europe/Zurich')::date
having count(*) > 0
on conflict (day, name) do update set n = e.n + excluded.n;

-- ---------- what the admin page reads: same functions, with real activity
create or replace function public.admin_overview()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare today date := (now() at time zone 'Europe/Zurich')::date; out jsonb;
begin
  if not public.is_admin() then raise exception 'not allowed' using errcode = '42501'; end if;
  with seen as (
    select greatest(u.last_sign_in_at, a.last_seen_at) t
    from auth.users u left join public.account_activity a on a.user_id = u.id)
  select jsonb_build_object(
    'now', now(),
    'users', (select count(*) from auth.users),
    'users_confirmed', (select count(*) from auth.users where email_confirmed_at is not null),
    'users_today', (select count(*) from auth.users where (created_at at time zone 'Europe/Zurich')::date = today),
    'users_7d', (select count(*) from auth.users where created_at > now() - interval '7 days'),
    'users_30d', (select count(*) from auth.users where created_at > now() - interval '30 days'),
    'active_today', (select count(*) from seen where (t at time zone 'Europe/Zurich')::date = today),
    'active_7d', (select count(*) from seen where t > now() - interval '7 days'),
    'active_30d', (select count(*) from seen where t > now() - interval '30 days'),
    'founding', (select count(*) from public.founding_waitlist where status = 'confirmed'),
    'founding_left', (select count(*) from public.founding_waitlist where status = 'unsubscribed'),
    'signups_by_day', coalesce((select jsonb_agg(jsonb_build_object('day', d, 'n', n) order by d) from (
        select (created_at at time zone 'Europe/Zurich')::date d, count(*) n from auth.users
        where created_at > now() - interval '60 days' group by 1) x), '[]'::jsonb),
    'founding_by_day', coalesce((select jsonb_agg(jsonb_build_object('day', d, 'n', n) order by d) from (
        select (confirmed_at at time zone 'Europe/Zurich')::date d, count(*) n from public.founding_waitlist
        where status = 'confirmed' and confirmed_at > now() - interval '60 days' group by 1) x), '[]'::jsonb),
    'signup_sources', coalesce((select jsonb_object_agg(s, n) from (
        select coalesce(raw_user_meta_data ->> 'signup_source', 'direct') s, count(*) n from auth.users group by 1) x), '{}'::jsonb),
    'founding_sources', coalesce((select jsonb_object_agg(s, n) from (
        select coalesce(source, 'direct') s, count(*) n from public.founding_waitlist where status = 'confirmed' group by 1) x), '{}'::jsonb),
    'events_by_day', coalesce((select jsonb_agg(jsonb_build_object('day', day, 'name', name, 'n', n) order by day) from public.site_events
        where day > today - 60), '[]'::jsonb),
    'events_total', coalesce((select jsonb_object_agg(name, n) from (select name, sum(n) n from public.site_events group by 1) x), '{}'::jsonb),
    'items', coalesce((select jsonb_object_agg(kind, n) from (select kind, count(*) n from public.atlas_items where not deleted group by 1) x), '{}'::jsonb),
    'levels', coalesce((select jsonb_object_agg(l, n) from (select coalesce(level, 'not set') l, count(*) n from public.profiles group by 1) x), '{}'::jsonb),
    'studying', coalesce((select jsonb_agg(jsonb_build_object('s', s, 'n', n) order by n desc) from (
        select studying s, count(*) n from public.profiles where coalesce(studying, '') <> '' group by 1 order by 2 desc limit 12) x), '[]'::jsonb),
    'top_saved', coalesce((select jsonb_agg(jsonb_build_object('id', item_id, 'n', n) order by n desc) from (
        select item_id, count(*) n from public.atlas_items where kind = 'saved' and not deleted group by 1 order by 2 desc limit 15) x), '[]'::jsonb)
  ) into out;
  return out;
end $$;

-- last_sign_in_at stays in the result, so the admin page online today keeps working until the new one is deployed
drop function public.admin_users();
create function public.admin_users()
returns table (email text, created_at timestamptz, last_sign_in_at timestamptz, last_seen_at timestamptz, confirmed boolean, signup_source text,
               founding_spot integer, display_name text, level text, studying text, location text,
               saved integer, tastings integer, notes integer, study integer)
language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.is_admin() then raise exception 'not allowed' using errcode = '42501'; end if;
  return query
  select u.email::text, u.created_at, u.last_sign_in_at, greatest(u.last_sign_in_at, a.last_seen_at), u.email_confirmed_at is not null,
         coalesce(u.raw_user_meta_data ->> 'signup_source', 'direct'),
         (select (select count(*)::integer from public.founding_waitlist c where c.status = 'confirmed' and c.position <= w.position)
            from public.founding_waitlist w where w.status = 'confirmed' and lower(w.email::text) = lower(u.email)),
         p.display_name, p.level, p.studying, p.location,
         (select count(*)::integer from public.atlas_items i where i.user_id = u.id and i.kind = 'saved' and not i.deleted),
         (select count(*)::integer from public.atlas_items i where i.user_id = u.id and i.kind = 'tasting' and not i.deleted),
         (select count(*)::integer from public.atlas_items i where i.user_id = u.id and i.kind = 'note' and not i.deleted),
         (select count(*)::integer from public.atlas_items i where i.user_id = u.id and i.kind = 'study' and not i.deleted)
  from auth.users u
  left join public.profiles p on p.id = u.id
  left join public.account_activity a on a.user_id = u.id
  order by u.created_at desc;
end $$;

revoke all on function public.touch_seen(), public.admin_overview(), public.admin_users() from public, anon, authenticated;
grant execute on function public.touch_seen(), public.admin_overview(), public.admin_users() to authenticated;
