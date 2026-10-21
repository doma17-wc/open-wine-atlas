// Public settings for the browser. The publishable key is meant to be public: row level security in the database
// decides what each signed-in user can read and write.
//   accountsOpen  sign-in, profile and sync (needs the Resend SMTP in Supabase Auth, see supabase/README.md)
//   foundingOpen  the Founding Member form (its emails also go through Resend)
// While a switch is off the page says it opens soon, and everything in My atlas keeps working on the device.
window.OWA_CONFIG = {
  supabaseUrl: "https://budizvexjzlbzzcmlaey.supabase.co",
  supabaseKey: "sb_publishable_Szh5zLItBA6cXPWAGtG3FQ_gD5QKDuN",
  accountsOpen: false,
  foundingOpen: false,
};
