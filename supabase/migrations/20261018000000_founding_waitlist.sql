-- Founding Member waitlist: one row per email, double opt-in.
-- Only the `founding` Edge Function (service role) reads or writes these tables. No public access.

create extension if not exists citext with schema extensions;

create table public.founding_waitlist (
  id              uuid primary key default gen_random_uuid(),
  email           extensions.citext not null unique,
  status          text not null default 'pending' check (status in ('pending', 'confirmed', 'unsubscribed')),
  token_hash      text not null unique,          -- sha256 of the token in the email link; the token itself is never stored
  position        integer unique,                -- order of confirmation; 1..1000 are Founding spots
  source          text,                          -- reel campaign, referrer or "direct"
  lang            text,
  ip_hash         text,                          -- keyed hash, only for rate limiting
  consent_version text not null,
  created_at      timestamptz not null default now(),
  email_sent_at   timestamptz,
  email_attempts  integer not null default 0,
  confirmed_at    timestamptz,
  unsubscribed_at timestamptz
);

create index founding_waitlist_ip_recent on public.founding_waitlist (ip_hash, created_at);
create index founding_waitlist_unsent on public.founding_waitlist (created_at) where status = 'pending' and email_sent_at is null;

create sequence public.founding_position_seq;

-- small key/value table so the function can throttle its own background work
create table public.founding_meta (k text primary key, v text, updated_at timestamptz not null default now());

alter table public.founding_waitlist enable row level security;
alter table public.founding_meta enable row level security;
revoke all on public.founding_waitlist, public.founding_meta from anon, authenticated;
revoke all on sequence public.founding_position_seq from anon, authenticated;

-- Confirm atomically: the first confirmation takes the next position, later clicks return the same one.
create or replace function public.founding_confirm(p_token_hash text)
-- out_rank is the place among members who are confirmed now (people who leave free their spot), so rank <= 1000
-- means a Founding spot.
returns table (out_position integer, out_rank integer)
language plpgsql security definer set search_path = public as $$
declare p integer;
begin
  update public.founding_waitlist w
     set status = 'confirmed',
         confirmed_at = coalesce(w.confirmed_at, now()),
         unsubscribed_at = null,
         position = coalesce(w.position, nextval('public.founding_position_seq'))
   where w.token_hash = p_token_hash and w.status in ('pending', 'confirmed')
  returning w.position into p;
  if p is null then return; end if;
  return query select p, (select count(*)::integer from public.founding_waitlist
                           where status = 'confirmed' and position <= p);
end $$;

create or replace function public.founding_count()
returns integer language sql stable security definer set search_path = public as $$
  select count(*)::integer from public.founding_waitlist where status = 'confirmed';
$$;

revoke all on function public.founding_confirm(text), public.founding_count() from public, anon, authenticated;
grant execute on function public.founding_confirm(text), public.founding_count() to service_role;
