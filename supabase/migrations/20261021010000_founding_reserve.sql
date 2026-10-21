-- One path for Founding Members: a signed-in user reserves a spot with the email of the account. The email is
-- already verified by the sign-in code, so the spot is confirmed at once (no second email). Returns the place
-- among confirmed members, like founding_confirm.
create or replace function public.founding_reserve(p_consent_version text, p_source text default null, p_lang text default null)
returns table (spot integer, founding boolean)
language plpgsql security definer set search_path = '' as $$
declare e text := lower(auth.jwt() ->> 'email'); p integer;
begin
  if auth.uid() is null or e is null then raise exception 'not signed in'; end if;
  insert into public.founding_waitlist as w (email, status, token_hash, position, source, lang, consent_version, confirmed_at, email_sent_at)
  values (e, 'confirmed', encode(extensions.gen_random_bytes(32), 'hex'), nextval('public.founding_position_seq'),
          left(p_source, 80), left(p_lang, 12), left(coalesce(p_consent_version, ''), 20), now(), now())
  on conflict (email) do update
    set status = 'confirmed',
        position = coalesce(w.position, excluded.position),
        confirmed_at = coalesce(w.confirmed_at, now()),
        unsubscribed_at = null,
        consent_version = excluded.consent_version
  returning w.position into p;
  return query select r, r <= 1000 from (select count(*)::integer as r from public.founding_waitlist
                                         where status = 'confirmed' and position <= p) x;
end $$;

revoke all on function public.founding_reserve(text, text, text) from public, anon;
grant execute on function public.founding_reserve(text, text, text) to authenticated;
