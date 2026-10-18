// Founding Member waitlist, double opt-in. Deployed with verify_jwt = false: the page calls it without a key,
// so every input is checked here and the database is reached only with the service role.
//
//   GET  ?action=count                         -> { confirmed, limit }
//   POST { action: "signup", email, consent, website, source, lang }
//   POST { action: "confirm", token }          -> { ok, position, founding }
//   POST { action: "unsubscribe", token }
//
// Emails go out through Resend (secret RESEND_API_KEY). If Resend is not set up yet, or its daily quota is used up,
// the signup is still stored and the email is sent later: every count or signup call works through a few queued
// rows, at most once every five minutes. Links in emails point to the site, never to this function.
import { createClient } from "npm:@supabase/supabase-js@2";

const SITE = "https://openwineatlas.com";
const FROM = "Open Wine Atlas <hello@openwineatlas.com>";
const REPLY_TO = "hello@openwineatlas.com";
const LIMIT = 1000;
const CONSENT_VERSION = "2026-10-18";
const PER_IP_PER_HOUR = 5;
const MAX_ATTEMPTS = 3; // emails per address per signup round, so nobody can flood an inbox
const QUEUE_BATCH = 20;

const URL_ = Deno.env.get("SUPABASE_URL")!;
const SERVICE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const RESEND = Deno.env.get("RESEND_API_KEY") || "";
const db = createClient(URL_, SERVICE, { auth: { persistSession: false } });

const ORIGINS = [/^https:\/\/(www\.)?openwineatlas\.com$/, /^https:\/\/open-wine-atlas(-[a-z0-9-]+)?\.vercel\.app$/, /^http:\/\/localhost(:\d+)?$/];
function cors(req: Request): Record<string, string> {
  const o = req.headers.get("origin") || "";
  return {
    "Access-Control-Allow-Origin": ORIGINS.some((r) => r.test(o)) ? o : SITE,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Vary": "Origin",
  };
}
const json = (req: Request, body: unknown, status = 200, extra: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...cors(req), ...extra } });

const enc = new TextEncoder();
const hex = (b: ArrayBuffer) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
const sha256 = async (s: string) => hex(await crypto.subtle.digest("SHA-256", enc.encode(s)));
async function hmac(s: string) {
  const key = await crypto.subtle.importKey("raw", enc.encode(SERVICE), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", key, enc.encode(s)));
}
function newToken() {
  const b = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
const EMAIL_RE = /^[^\s@<>()",;:]+@[^\s@<>()",;:]+\.[A-Za-z]{2,}$/;
// deno-lint-ignore no-control-regex
const clean = (v: unknown, n: number) => (typeof v === "string" ? v.replace(/[\u0000-\u001f<>]/g, "").trim().slice(0, n) : null);

// ---------- email
function mailFor(token: string) {
  const confirm = `${SITE}/founding?confirm=${token}`;
  const unsub = `${SITE}/founding?unsubscribe=${token}`;
  const text = [
    "Confirm your Founding Member spot",
    "",
    "Thanks for reserving a spot at Open Wine Atlas. Open this link to confirm your email:",
    confirm,
    "",
    "Founding price: CHF 19 for the first year, then CHF 39 a year for as long as you stay. Nothing to pay now.",
    "",
    "If you did not ask for this, ignore this email and nothing happens.",
    "",
    "Open Wine Atlas, openwineatlas.com",
    `Privacy: ${SITE}/privacy`,
    `Leave the list: ${unsub}`,
  ].join("\n");
  const html = `<!doctype html><html><body style="margin:0;background:#0b0b0d;padding:32px 16px;font-family:Helvetica,Arial,sans-serif;color:#e6dccb">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td align="center">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:520px;background:#141417;border:1px solid #2a2a31;border-radius:12px">
<tr><td style="padding:32px 28px 8px;font-family:Georgia,serif;font-size:22px;color:#e6dccb">Open Wine Atlas</td></tr>
<tr><td style="padding:8px 28px 0;font-family:Georgia,serif;font-size:30px;line-height:1.15;color:#e7c06a">Confirm your Founding Member spot</td></tr>
<tr><td style="padding:18px 28px 0;font-size:15px;line-height:1.6;color:#cfc6b6">Thanks for reserving a spot. Confirm your email to hold it.</td></tr>
<tr><td style="padding:24px 28px"><a href="${confirm}" style="display:inline-block;background:#e7c06a;color:#0b0b0d;text-decoration:none;font-weight:bold;font-size:15px;padding:13px 22px;border-radius:8px">Confirm my spot</a></td></tr>
<tr><td style="padding:0 28px;font-size:14px;line-height:1.6;color:#cfc6b6">Founding price: CHF 19 for the first year, then CHF 39 a year for as long as you stay. Nothing to pay now.</td></tr>
<tr><td style="padding:16px 28px 28px;font-size:13px;line-height:1.6;color:#8d877c">If you did not ask for this, ignore this email and nothing happens.</td></tr>
</table>
<p style="max-width:520px;font-size:12px;line-height:1.6;color:#8d877c;margin:16px auto 0">Open Wine Atlas &middot; <a href="${SITE}" style="color:#8d877c">openwineatlas.com</a> &middot; <a href="${SITE}/privacy" style="color:#8d877c">Privacy</a> &middot; <a href="${unsub}" style="color:#8d877c">Leave the list</a></p>
</td></tr></table></body></html>`;
  return { subject: "Confirm your Founding Member spot", text, html, unsub };
}

// "sent" | "quota" (stop for now) | "failed"
async function sendConfirm(email: string, token: string): Promise<"sent" | "quota" | "failed"> {
  if (!RESEND) return "quota";
  const m = mailFor(token);
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${RESEND}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: FROM, to: [email], reply_to: REPLY_TO, subject: m.subject, text: m.text, html: m.html,
      headers: { "List-Unsubscribe": `<${m.unsub}>` },
    }),
  }).catch(() => null);
  if (!r) return "failed";
  if (r.ok) return "sent";
  if (r.status === 429) return "quota";
  console.error("resend", r.status, await r.text().catch(() => ""));
  return "failed";
}

// give a pending row a fresh token and email it
async function issueAndSend(id: string, email: string, attempts: number) {
  const token = newToken();
  await db.from("founding_waitlist").update({ token_hash: await sha256(token) }).eq("id", id);
  const res = await sendConfirm(email, token);
  if (res === "sent") await db.from("founding_waitlist").update({ email_sent_at: new Date().toISOString(), email_attempts: attempts + 1 }).eq("id", id);
  else if (res === "failed") await db.from("founding_waitlist").update({ email_attempts: attempts + 1 }).eq("id", id);
  return res;
}

// work through emails that could not go out yet (no key, quota), throttled
async function drainQueue() {
  const { data: m } = await db.from("founding_meta").select("v").eq("k", "queue_at").maybeSingle();
  if (m?.v && Date.now() - Date.parse(m.v) < 5 * 60 * 1000) return;
  await db.from("founding_meta").upsert({ k: "queue_at", v: new Date().toISOString(), updated_at: new Date().toISOString() });
  // unconfirmed signups are deleted after 30 days, as the privacy policy says
  await db.from("founding_waitlist").delete().eq("status", "pending").lt("created_at", new Date(Date.now() - 30 * 864e5).toISOString());
  if (!RESEND) return;
  const since = new Date(Date.now() - 14 * 864e5).toISOString();
  const { data: rows } = await db.from("founding_waitlist").select("id,email,email_attempts")
    .eq("status", "pending").is("email_sent_at", null).lt("email_attempts", MAX_ATTEMPTS).gt("created_at", since)
    .order("created_at").limit(QUEUE_BATCH);
  for (const r of rows || []) {
    if ((await issueAndSend(r.id, r.email, r.email_attempts)) === "quota") break;
    await new Promise((ok) => setTimeout(ok, 600)); // stay under Resend's request rate
  }
}

// keep the function alive for work that finishes after the response
// deno-lint-ignore no-explicit-any
const ER = (globalThis as any).EdgeRuntime;
function background(p: Promise<unknown>) {
  const q = p.catch((e) => console.error("background", e));
  if (ER?.waitUntil) ER.waitUntil(q);
}

// ---------- actions
async function count(req: Request) {
  const { data } = await db.rpc("founding_count");
  background(drainQueue());
  return json(req, { confirmed: data ?? 0, limit: LIMIT }, 200, { "Cache-Control": "public, max-age=60" });
}

async function signup(req: Request, b: Record<string, unknown>) {
  if (clean(b.website, 200)) return json(req, { ok: true }); // honeypot: pretend it worked
  const email = (clean(b.email, 254) || "").toLowerCase();
  if (!EMAIL_RE.test(email)) return json(req, { ok: false, error: "invalid_email" }, 400);
  if (b.consent !== true) return json(req, { ok: false, error: "consent_required" }, 400);

  const ip = (req.headers.get("x-forwarded-for") || "").split(",")[0].trim() || "unknown";
  const ipHash = await hmac("ip:" + ip);
  const hourAgo = new Date(Date.now() - 3600e3).toISOString();
  const { count: recent } = await db.from("founding_waitlist").select("id", { count: "exact", head: true })
    .eq("ip_hash", ipHash).gt("created_at", hourAgo);
  if ((recent ?? 0) >= PER_IP_PER_HOUR) return json(req, { ok: false, error: "rate_limited" }, 429);

  const { data: row } = await db.from("founding_waitlist").select("id,status,email_attempts").eq("email", email).maybeSingle();
  // The answer is the same whether or not the address is known, so the form cannot be used to test who signed up.
  if (row?.status === "confirmed") return json(req, { ok: true });
  if (row && row.status === "pending") {
    if (row.email_attempts < MAX_ATTEMPTS) await issueAndSend(row.id, email, row.email_attempts);
    return json(req, { ok: true });
  }
  const fields = {
    source: clean(b.source, 80), lang: clean(b.lang, 12), ip_hash: ipHash, consent_version: CONSENT_VERSION,
    email_sent_at: null, email_attempts: 0,
  };
  let id = row?.id as string | undefined;
  if (row) { // came back after leaving the list
    await db.from("founding_waitlist").update({ ...fields, status: "pending", unsubscribed_at: null, created_at: new Date().toISOString() }).eq("id", row.id);
  } else {
    const { data: ins, error } = await db.from("founding_waitlist")
      .insert({ ...fields, email, token_hash: await sha256(newToken()) }).select("id").single();
    if (error) { // a second request for the same address raced this one
      if (error.code === "23505") return json(req, { ok: true });
      console.error("insert", error); return json(req, { ok: false, error: "server" }, 500);
    }
    id = ins.id;
  }
  await issueAndSend(id!, email, 0);
  background(drainQueue());
  return json(req, { ok: true });
}

async function confirm(req: Request, b: Record<string, unknown>) {
  const token = clean(b.token, 100);
  if (!token) return json(req, { ok: false, error: "invalid_token" }, 400);
  const { data, error } = await db.rpc("founding_confirm", { p_token_hash: await sha256(token) });
  if (error) { console.error("confirm", error); return json(req, { ok: false, error: "server" }, 500); }
  const r = Array.isArray(data) ? data[0] : data;
  if (!r) return json(req, { ok: false, error: "invalid_token" }, 404);
  return json(req, { ok: true, position: r.out_rank, founding: r.out_rank <= LIMIT });
}

async function unsubscribe(req: Request, b: Record<string, unknown>) {
  const token = clean(b.token, 100);
  if (!token) return json(req, { ok: false, error: "invalid_token" }, 400);
  const { data } = await db.from("founding_waitlist")
    .update({ status: "unsubscribed", unsubscribed_at: new Date().toISOString() })
    .eq("token_hash", await sha256(token)).neq("status", "unsubscribed").select("id");
  if (data?.length) return json(req, { ok: true });
  const { data: was } = await db.from("founding_waitlist").select("id").eq("token_hash", await sha256(token)).maybeSingle();
  return was ? json(req, { ok: true }) : json(req, { ok: false, error: "invalid_token" }, 404);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(req) });
  try {
    const url = new URL(req.url);
    if (req.method === "GET" && url.searchParams.get("action") === "count") return await count(req);
    if (req.method !== "POST") return json(req, { ok: false, error: "method" }, 405);
    if ((Number(req.headers.get("content-length")) || 0) > 4096) return json(req, { ok: false, error: "too_large" }, 413);
    const b = await req.json().catch(() => ({})) as Record<string, unknown>;
    if (b.action === "signup") return await signup(req, b);
    if (b.action === "confirm") return await confirm(req, b);
    if (b.action === "unsubscribe") return await unsubscribe(req, b);
    return json(req, { ok: false, error: "unknown_action" }, 400);
  } catch (e) {
    console.error(e);
    return json(req, { ok: false, error: "server" }, 500);
  }
});
