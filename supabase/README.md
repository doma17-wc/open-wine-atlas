# Supabase backend

Two parts, both in one Supabase project (region Zurich, `eu-central-2`):

* `migrations/20261018000000_founding_waitlist.sql` and `functions/founding`: the Founding Member waitlist (double
  opt-in emails through Resend, secret `RESEND_API_KEY`).
* `migrations/20261018010000_accounts.sql` and `web/account.js`: accounts. Profiles and everything from My atlas
  (saved places, tastings, notes, recent, compare) in `atlas_items`, each user limited to their own rows by row level
  security.

The browser reads the project URL and the publishable key from `web/config.js`.

## Settings made in the Supabase dashboard

* Authentication > URL configuration: Site URL `https://openwineatlas.com`; redirect URLs
  `https://openwineatlas.com/**`, `https://open-wine-atlas.vercel.app/**`, `https://open-wine-atlas-*-wncr.vercel.app/**`.
* Authentication > Emails > SMTP: Resend (`smtp.resend.com`, port 465, user `resend`, password = Resend API key),
  sender `Open Wine Atlas <hello@openwineatlas.com>`.
* Authentication > Emails > templates "Magic link" and "Confirm signup": `templates/sign-in-code.html`, so the
  email carries a code as well as the link (the link only works on the device that asked for it).
* Edge Function `founding`: deployed with JWT verification off; it checks every request itself.
