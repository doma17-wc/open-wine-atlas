# Supabase backend

Two parts, both in one Supabase project (region Zurich, `eu-central-2`):

* `migrations/20261018000000_founding_waitlist.sql` and `functions/founding`: the Founding Member waitlist (double
  opt-in emails through Resend, secret `RESEND_API_KEY`).
* `migrations/20261018010000_accounts.sql` and `web/account.js`: accounts. Profiles and everything from My atlas
  (saved places, tastings, notes, recent, compare) in `atlas_items`, each user limited to their own rows by row level
  security.

The browser reads the project URL and the publishable key from `web/config.js`, with two switches: `accountsOpen`
(sign-in, profile, sync) and `foundingOpen` (the Founding form). Both stay `false` until the email settings below
are done; meanwhile My atlas, the notebook and the study work on the device, and /founding says it opens soon.

## Status (21 October 2026)

Project `budizvexjzlbzzcmlaey` ("Open Wine Atlas", Zurich). Applied: the waitlist, accounts and study migrations;
the `founding` function is deployed with JWT verification off. Still to do, in this order:

1. In the SQL editor, run the `delete_my_account()` part of `20261018010000_accounts.sql` (the API refused to apply
   a statement that deletes from `auth.users` without a confirmation, so it was left out).
2. Resend: verify `openwineatlas.com` (DNS records at GoDaddy) and create an API key.
3. Edge Functions > Secrets: `RESEND_API_KEY`.
4. The Authentication settings below.
5. `web/config.js`: `accountsOpen: true`, `foundingOpen: true`, then rebuild and deploy.

## Settings made in the Supabase dashboard

* Authentication > URL configuration: Site URL `https://openwineatlas.com`; redirect URLs
  `https://openwineatlas.com/**`, `https://open-wine-atlas.vercel.app/**`, `https://open-wine-atlas-*-wncr.vercel.app/**`.
* Authentication > Emails > SMTP: Resend (`smtp.resend.com`, port 465, user `resend`, password = Resend API key),
  sender `Open Wine Atlas <hello@openwineatlas.com>`.
* Authentication > Emails > templates "Magic link" and "Confirm signup": `templates/sign-in-code.html`, so the
  email carries a code as well as the link (the link only works on the device that asked for it).
* Edge Function `founding`: deployed with JWT verification off; it checks every request itself.
