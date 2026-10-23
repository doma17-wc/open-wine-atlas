-- Admin: one page (web/admin.html) where the owner sees what happens on the atlas. Nothing here is public:
-- every admin function checks the signed-in email against public.admins, and the page shows nothing without it.
--
-- Also small daily counters for a few steps of the sign-up path (the Burgundy preview and wall, the Founding page).
-- Plain totals per day: no user, no IP, no cookie.

create table public.admins (email extensions.citext primary key, added_at timestamptz not null default now());
alter table public.admins enable row level security;
revoke all on public.admins from anon, authenticated;
insert into public.admins (email) values ('stefano.paolino1@gmail.com');

create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.admins a where a.email = (auth.jwt() ->> 'email')::extensions.citext);
$$;

-- ---------- daily counters
create table public.site_events (
  day  date not null default (now() at time zone 'Europe/Zurich')::date,
  name text not null,
  n    integer not null default 0,
  primary key (day, name)
);
alter table public.site_events enable row level security;
revoke all on public.site_events from anon, authenticated;

create or replace function public.track(p_name text)
returns void language plpgsql security definer set search_path = '' as $$
begin
  -- only the known steps are counted, so the table cannot be filled with anything else
  if p_name not in ('deep_preview', 'deep_wall', 'deep_join', 'founding_view') then return; end if;
  insert into public.site_events as e (name, n) values (p_name, 1)
  on conflict (day, name) do update set n = e.n + 1;
end $$;

-- ---------- what the admin page reads
create or replace function public.admin_overview()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare today date := (now() at time zone 'Europe/Zurich')::date; out jsonb;
begin
  if not public.is_admin() then raise exception 'not allowed' using errcode = '42501'; end if;
  select jsonb_build_object(
    'now', now(),
    'users', (select count(*) from auth.users),
    'users_confirmed', (select count(*) from auth.users where email_confirmed_at is not null),
    'users_today', (select count(*) from auth.users where (created_at at time zone 'Europe/Zurich')::date = today),
    'users_7d', (select count(*) from auth.users where created_at > now() - interval '7 days'),
    'users_30d', (select count(*) from auth.users where created_at > now() - interval '30 days'),
    'active_7d', (select count(*) from auth.users where last_sign_in_at > now() - interval '7 days'),
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

create or replace function public.admin_users()
returns table (email text, created_at timestamptz, last_sign_in_at timestamptz, confirmed boolean, signup_source text,
               founding_spot integer, display_name text, level text, studying text, location text,
               saved integer, tastings integer, notes integer, study integer)
language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.is_admin() then raise exception 'not allowed' using errcode = '42501'; end if;
  return query
  select u.email::text, u.created_at, u.last_sign_in_at, u.email_confirmed_at is not null,
         coalesce(u.raw_user_meta_data ->> 'signup_source', 'direct'),
         (select (select count(*)::integer from public.founding_waitlist c where c.status = 'confirmed' and c.position <= w.position)
            from public.founding_waitlist w where w.status = 'confirmed' and lower(w.email::text) = lower(u.email)),
         p.display_name, p.level, p.studying, p.location,
         (select count(*)::integer from public.atlas_items i where i.user_id = u.id and i.kind = 'saved' and not i.deleted),
         (select count(*)::integer from public.atlas_items i where i.user_id = u.id and i.kind = 'tasting' and not i.deleted),
         (select count(*)::integer from public.atlas_items i where i.user_id = u.id and i.kind = 'note' and not i.deleted),
         (select count(*)::integer from public.atlas_items i where i.user_id = u.id and i.kind = 'study' and not i.deleted)
  from auth.users u left join public.profiles p on p.id = u.id
  order by u.created_at desc;
end $$;

revoke all on function public.is_admin(), public.track(text), public.admin_overview(), public.admin_users() from public, anon, authenticated;
grant execute on function public.track(text) to anon, authenticated;
grant execute on function public.is_admin(), public.admin_overview(), public.admin_users() to authenticated;
