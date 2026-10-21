-- Accounts: a profile per user and everything from My atlas (saved places, tastings, notes, recent, compare),
-- so it is the same on every device. The site stays usable without an account: My atlas keeps working on the
-- device, and signing in only adds sync.
--
-- One generic table holds the items. Each item is (kind, item_id) for a user, with its data as JSON, as the page
-- already keeps it. Deleting writes a tombstone (deleted = true) so other devices learn about it. updated_at is set
-- by the server and is the cursor devices pull from.

-- ---------- profiles
create table public.profiles (
  id               uuid primary key references auth.users (id) on delete cascade,
  display_name     text check (char_length(display_name) <= 60),
  level            text check (level in ('enthusiast', 'student', 'sommelier', 'trade', 'winemaker', 'other')),
  studying         text check (char_length(studying) <= 60),     -- e.g. "WSET Level 3", free text
  location         text check (char_length(location) <= 60),     -- free text, e.g. "Zurich, Switzerland"
  bio              text check (char_length(bio) <= 500),
  favourite_places text[] not null default '{}' check (cardinality(favourite_places) <= 12),
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id) values (new.id) on conflict (id) do nothing;
  return new;
end $$;

create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------- My atlas items
create table public.atlas_items (
  user_id    uuid not null default auth.uid() references auth.users (id) on delete cascade,
  kind       text not null check (kind in ('saved', 'tasting', 'note', 'state')),
  item_id    text not null check (char_length(item_id) between 1 and 120),
  data       jsonb not null default '{}'::jsonb check (pg_column_size(data) <= 65536),
  deleted    boolean not null default false,
  updated_at timestamptz not null default now(),
  primary key (user_id, kind, item_id)
);
create index atlas_items_user_updated on public.atlas_items (user_id, updated_at);

create or replace function public.touch_updated_at()
returns trigger language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  return new;
end $$;

create or replace function public.atlas_items_before_write()
returns trigger language plpgsql set search_path = '' as $$
begin
  new.updated_at := clock_timestamp();
  if new.deleted then new.data := '{}'::jsonb; end if;
  if tg_op = 'INSERT' and (select count(*) from public.atlas_items where user_id = new.user_id) >= 20000 then
    raise exception 'item limit reached' using errcode = 'P0001';
  end if;
  return new;
end $$;

create trigger atlas_items_write before insert or update on public.atlas_items
  for each row execute function public.atlas_items_before_write();
create trigger profiles_touch before update on public.profiles
  for each row execute function public.touch_updated_at();

-- ---------- row level security: every user sees and changes only their own rows
alter table public.profiles enable row level security;
alter table public.atlas_items enable row level security;

create policy "own profile: read"   on public.profiles for select to authenticated using ((select auth.uid()) = id);
create policy "own profile: update" on public.profiles for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

create policy "own items: read"   on public.atlas_items for select to authenticated using ((select auth.uid()) = user_id);
create policy "own items: insert" on public.atlas_items for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "own items: update" on public.atlas_items for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "own items: delete" on public.atlas_items for delete to authenticated using ((select auth.uid()) = user_id);

revoke all on public.profiles, public.atlas_items from anon;
grant select, update on public.profiles to authenticated;
grant select, insert, update, delete on public.atlas_items to authenticated;

-- ---------- Founding Member badge: the signed-in user's confirmed spot on the waitlist, if any
create or replace function public.my_founding()
returns table (spot integer, founding boolean)
language sql stable security definer set search_path = '' as $$
  select r.rank, r.rank <= 1000
  from (select w.email, (select count(*)::integer from public.founding_waitlist c
                          where c.status = 'confirmed' and c.position <= w.position) as rank
          from public.founding_waitlist w
         where w.status = 'confirmed' and lower(w.email::text) = lower(auth.jwt() ->> 'email')) r;
$$;

-- ---------- delete my account: removes the user, the profile and every item (cascade)
create or replace function public.delete_my_account()
returns void language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  delete from auth.users where id = auth.uid();
end $$;

revoke all on function public.my_founding(), public.delete_my_account(), public.handle_new_user() from public, anon;
grant execute on function public.my_founding(), public.delete_my_account() to authenticated;
