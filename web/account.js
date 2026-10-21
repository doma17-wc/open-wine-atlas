// Open Wine Atlas: account, profile and sync (web only).
//
// My atlas keeps working on the device without an account. Signing in (email code, no password) adds a profile and
// keeps saved places, tastings, notes, recent places and the compare list the same on every device.
//
// Sync: every item is a row (kind, item_id, data) in atlas_items, guarded by row level security. The device keeps a
// small fingerprint of what the server last had, so it knows what changed here (send it), what was removed here
// (send a tombstone) and pulls what changed elsewhere since its last cursor. The server's copy wins when both changed.
// The Supabase client is loaded from the CDN only when it is needed.
(() => {
"use strict";
const O = window.OWA;
if (!O || window.OWA_ACCOUNT) return;
const { MY, esc, t_ } = O;
const $ = (id) => document.getElementById(id);
const SB_JS = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js";
const AUTH_KEY = "owa.auth", META_KEY = "owa.sync";
const PAGE = 1000, CHUNK = 400;

// ---------- what is synced: each kind maps to one or two lists of My atlas
const KINDS = {
  saved:   { keys: ["saved"],   items: () => Object.entries(MY.saved),             apply: (m) => { MY.saved = Object.fromEntries(m); } },
  tasting: { keys: ["journal"], items: () => MY.journal.map((j) => [j.at, j]),     apply: (m) => { MY.journal = [...m.values()]; } },
  note:    { keys: ["notes"],   items: () => MY.notes.map((n) => [n.id, n]),       apply: (m) => { MY.notes = [...m.values()]; } },
  state:   { keys: ["recent", "compare"], keep: true,
             items: () => [["recent", { v: MY.recent }], ["compare", { v: MY.compare }]],
             apply: (m) => { if (m.get("recent")) MY.recent = m.get("recent").v || []; if (m.get("compare")) MY.compare = m.get("compare").v || []; } },
};
// study progress (study.js): one row per review card, plus the lessons read and the totals
KINDS.study = { keys: ["study"], keep: true,
  items: () => { const s = MY.study || {};
    return [...Object.entries(s.cards || {}).map(([k, v]) => ["c:" + k, v]), ["done", { v: s.done || {} }], ["stats", { v: s.stats || {}, today: s.today || {} }]]; },
  apply: (m) => { const s = MY.study && typeof MY.study === "object" ? MY.study : (MY.study = {});
    s.cards = {}; for (const [id, v] of m) if (id.startsWith("c:")) s.cards[id.slice(2)] = v;
    if (m.get("done")) s.done = m.get("done").v || {};
    if (m.get("stats")) { s.stats = m.get("stats").v || s.stats; s.today = m.get("stats").today || s.today; } } };
const KIND_OF = { saved: "saved", journal: "tasting", notes: "note", recent: "state", compare: "state", study: "study" };

// a fingerprint that does not depend on key order (the database stores JSON keys in its own order)
const canon = (v) => Array.isArray(v) ? "[" + v.map(canon).join(",") + "]"
  : v && typeof v === "object" ? "{" + Object.keys(v).sort().filter((k) => v[k] !== undefined).map((k) => JSON.stringify(k) + ":" + canon(v[k])).join(",") + "}"
  : JSON.stringify(v ?? null);
function fp(o) { const s = canon(o); let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); } return (h >>> 0).toString(36) + "." + s.length.toString(36); }
const okId = (id) => typeof id === "string" && id.length > 0 && id.length <= 120;

// ---------- state
const S = { loading: null, loadFailed: false, sb: null, user: null, profile: null, founding: null, step: "email", email: "", msg: "", busy: false,
  sync: "idle", lastSync: 0, syncing: false, again: false, timer: 0, poll: 0, fav: null, confirmClear: false, dangerOpen: false, unavailable: false };
function loadMeta() { try { return JSON.parse(localStorage.getItem(META_KEY)) || {}; } catch (e) { return {}; } }
function saveMeta(m) { try { localStorage.setItem(META_KEY, JSON.stringify(m)); } catch (e) {} }
function clearMeta() { try { localStorage.removeItem(META_KEY); } catch (e) {} }
// one load per script: a second call waits for the first instead of returning before the script has run
const LOADS = new Map();
const loadScript = (src) => {
  if (!LOADS.has(src)) LOADS.set(src, new Promise((ok, fail) => {
    const s = document.createElement("script"); s.src = src; s.async = true; s.dataset.src = src; s.onload = ok;
    s.onerror = () => { LOADS.delete(src); fail(new Error("load " + src)); };
    document.head.appendChild(s);
  }));
  return LOADS.get(src);
};
function rerender() { if (O.tab === "account" || O.tab === "overview") O.renderDash(); }
const view = () => O.tab === "account";

// ---------- the Supabase client, loaded on demand
async function client() {
  if (S.sb) return S.sb;
  await loadScript("/config.js");
  const C = window.OWA_CONFIG;
  if (!C || !C.accountsOpen || /SUPABASE_REF|SUPABASE_PUBLISHABLE_KEY/.test(C.supabaseUrl + C.supabaseKey)) { S.unavailable = true; throw new Error("not_configured"); }
  await loadScript(SB_JS);
  S.sb = window.supabase.createClient(C.supabaseUrl, C.supabaseKey, {
    auth: { flowType: "pkce", persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, storageKey: AUTH_KEY },
  });
  // never await Supabase calls inside this callback: hand the work to the next tick
  S.sb.auth.onAuthStateChange((ev, session) => { setTimeout(() => onSession(session, ev), 0); });
  return S.sb;
}

async function onSession(session, ev) {
  const u = session?.user || null;
  if (u && (!S.user || S.user.id !== u.id)) {
    S.user = u; S.step = "email"; S.msg = "";
    const url = new URL(location.href);
    if (url.searchParams.has("code") || url.searchParams.has("signin")) {
      url.searchParams.delete("code"); url.searchParams.delete("signin");
      history.replaceState(null, "", url.pathname + url.search + url.hash);
      O.openDash("account");
      O.toast(t_("Signed in. Your atlas is syncing."));
    }
    await Promise.all([loadProfile(), loadFounding()]);
    rerender();
    fullSync();
    startPolling();
  } else if (!u && S.user) {
    S.user = null; S.profile = null; S.founding = null; S.sync = "idle"; stopPolling(); rerender();
  } else if (ev === "INITIAL_SESSION") rerender();
}

// ---------- profile
async function loadProfile() {
  const { data, error } = await S.sb.from("profiles").select("display_name,level,studying,location,bio,favourite_places").eq("id", S.user.id).maybeSingle();
  if (!error) { S.profile = data || {}; S.fav = [...(S.profile.favourite_places || [])]; }
}
async function loadFounding() {
  const { data } = await S.sb.rpc("my_founding");
  S.founding = Array.isArray(data) && data[0] ? data[0] : null;
}

// ---------- sync
function setSync(s) {
  S.sync = s; if (s === "ok") S.lastSync = Date.now();
  const el = $("acct-sync"); if (el) { el.textContent = syncText(); el.className = "acct-sync" + (s === "error" ? " err" : ""); }
}
function syncText() {
  if (S.sync === "syncing") return t_("Syncing…");
  if (S.sync === "error") return t_("Could not sync. It will try again.");
  if (S.sync === "ok") return t_("Synced {when}", { when: ago(S.lastSync) });
  return "";
}
function ago(t) {
  const s = Math.round((Date.now() - t) / 1000);
  if (s < 45) return t_("just now");
  if (s < 3600) return t_("{n} min ago", { n: Math.round(s / 60) });
  return new Date(t).toLocaleTimeString(O.LOCALE, { hour: "2-digit", minute: "2-digit" });
}

async function fullSync() {
  if (!S.user || !S.sb) return;
  if (S.syncing) { S.again = true; return; }
  S.syncing = true; setSync("syncing");
  try {
    let meta = loadMeta();
    if (meta.uid !== S.user.id) meta = { uid: S.user.id, cursor: null, h: {} }; // first sync of this account here: merge both ways
    await pushAll(meta);
    await pull(meta);
    saveMeta(meta);
    setSync("ok");
  } catch (e) {
    console.error("sync", e); setSync("error");
  }
  S.syncing = false;
  if (S.again) { S.again = false; fullSync(); }
}

// send what changed on this device since the last sync, and tombstones for what was removed here
async function pushAll(meta) {
  const rows = [], done = [];
  for (const [kind, K] of Object.entries(KINDS)) {
    const seen = meta.h[kind] || (meta.h[kind] = {});
    const local = new Map(K.items().filter(([id]) => okId(id)));
    for (const [id, obj] of local) {
      const f = fp(obj);
      if (seen[id] !== f) { rows.push({ user_id: S.user.id, kind, item_id: id, data: obj, deleted: false }); done.push([kind, id, f]); }
    }
    if (!K.keep) for (const id of Object.keys(seen)) if (!local.has(id)) { rows.push({ user_id: S.user.id, kind, item_id: id, data: {}, deleted: true }); done.push([kind, id, null]); }
  }
  for (let i = 0; i < rows.length; i += CHUNK) {
    const { error } = await S.sb.from("atlas_items").upsert(rows.slice(i, i + CHUNK), { onConflict: "user_id,kind,item_id" });
    if (error) throw error;
    done.slice(i, i + CHUNK).forEach(([kind, id, f]) => { if (f) meta.h[kind][id] = f; else delete meta.h[kind][id]; });
  }
}

// take what changed elsewhere since the cursor (with a few seconds of overlap for writes that commit late)
async function pull(meta) {
  const since = meta.cursor ? new Date(Date.parse(meta.cursor) - 5000).toISOString() : null;
  const maps = {}, changed = new Set();
  for (let from = 0; ; from += PAGE) {
    let q = S.sb.from("atlas_items").select("kind,item_id,data,deleted,updated_at").order("updated_at").order("item_id").range(from, from + PAGE - 1);
    if (since) q = q.gt("updated_at", since);
    const { data, error } = await q;
    if (error) throw error;
    for (const r of data) {
      const K = KINDS[r.kind]; if (!K) continue;
      const m = maps[r.kind] || (maps[r.kind] = new Map(K.items()));
      const seen = meta.h[r.kind] || (meta.h[r.kind] = {});
      if (r.deleted) {
        if (!K.keep && m.has(r.item_id)) { m.delete(r.item_id); changed.add(r.kind); }
        delete seen[r.item_id];
      } else {
        const f = fp(r.data);
        if (!m.has(r.item_id) || fp(m.get(r.item_id)) !== f) { m.set(r.item_id, r.data); changed.add(r.kind); }
        seen[r.item_id] = f;
      }
      if (!meta.cursor || r.updated_at > meta.cursor) meta.cursor = r.updated_at;
    }
    if (data.length < PAGE) break;
  }
  if (changed.size) {
    const keys = [];
    changed.forEach((kind) => { KINDS[kind].apply(maps[kind]); keys.push(...KINDS[kind].keys); });
    O.myChanged(keys);
  }
}

// local saves: sync a moment later, once the edits settle
O.onSave((k) => {
  if (!S.user || !KIND_OF[k]) return;
  clearTimeout(S.timer);
  S.timer = setTimeout(fullSync, k === "recent" ? 8000 : 1500);
});
function startPolling() {
  stopPolling();
  S.poll = setInterval(() => { if (document.visibilityState === "visible") fullSync(); else if (S.sync === "ok") setSync("ok"); }, 90000);
}
function stopPolling() { clearInterval(S.poll); S.poll = 0; }
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && S.user && Date.now() - S.lastSync > 20000) fullSync(); });

// ---------- views
const LEVELS = [["", N("Choose")], ["enthusiast", N("Wine lover")], ["student", N("Wine student")], ["sommelier", N("Sommelier")],
  ["trade", N("Wine trade")], ["winemaker", N("Winemaker")], ["other", N("Other")]];
const STUDY = ["WSET Level 1", "WSET Level 2", "WSET Level 3", "WSET Diploma", "Court of Master Sommeliers", "Master of Wine", "AIS", "ASI", "Self-taught"];
function N(s) { return s; }
const initial = () => ((S.profile?.display_name || S.user?.email || "?").trim()[0] || "?").toUpperCase();
const countList = (c) => [t_("saved places: {n}", { n: c.saved }), t_("tastings: {n}", { n: c.tastings }), t_("notes: {n}", { n: c.notes })].join(", ");
const counts = () => ({ saved: Object.keys(MY.saved).length, tastings: MY.journal.length, notes: MY.notes.length });

function line() {
  if (S.unavailable && !S.user) return "";
  if (S.user) return '<div class="acct-line"><span class="acct-av" style="width:26px;height:26px;font-size:13px">' + esc(initial()) + "</span><span>" +
    t_("Signed in as {name}", { name: "<b>" + esc(S.profile?.display_name || S.user.email) + "</b>" }) + "</span>" +
    (S.founding?.founding ? '<span class="badge-f">' + t_("Founding Member") + "</span>" : "") +
    '<button class="mini-btn" data-dash="account">' + t_("Account") + "</button></div>";
  return '<div class="acct-line"><button class="mini-btn" data-dash="account">' + t_("Sign in to keep your atlas on every device") + " →</button></div>";
}

function render() {
  if (S.unavailable) return '<div class="acct"><div class="empty">' + t_("Accounts are not open yet. Everything in My atlas keeps working on this device.") + "</div></div>";
  if (S.loadFailed) return '<div class="acct"><div class="empty">' + t_("The account service could not load. Check your connection.") + ' <button class="mini-btn" id="acct-retry">' + t_("Try again") + "</button></div></div>";
  if (!S.sb) {
    if (!S.loading) S.loading = client().then(() => S.sb.auth.getSession()).then(({ data }) => { if (!data.session) rerender(); })
      .catch((e) => { if (e.message !== "not_configured") S.loadFailed = true; rerender(); }).finally(() => { S.loading = null; });
    return '<p class="lead">' + t_("Loading…") + "</p>";
  }
  return '<div class="acct">' + (S.user ? signedIn() : signedOut()) + "</div>";
}

// the Terms of Use and age the sign-up form asks for; stored with a new account (user metadata)
const TERMS_VERSION = "2026-10-20";
const link = (href, text) => '<a href="' + href + '" target="_blank" rel="noopener" style="color:inherit">' + text + "</a>";
function signedOut() {
  const c = counts(), have = c.saved + c.tastings + c.notes;
  const intro = '<h3>' + t_("Your atlas on every device") + '</h3><p class="lead">' + t_("Sign in with your email. We send you a code, no password needed.") + " " +
    (have ? t_("What is on this device comes with you: {list}.", { list: countList(c) }) : t_("Your saved places, tastings and notes follow you from phone to laptop.")) + "</p>";
  if (S.step === "code") return '<div class="acct-card">' + intro +
    '<form class="jform" id="acct-code-form" autocomplete="off"><label class="wide">' + t_("We sent a code to {email}. Enter it here.", { email: "<b>" + esc(S.email) + "</b>" }) +
    '<input id="acct-code" class="code" inputmode="numeric" autocomplete="one-time-code" maxlength="10" placeholder="••••••" required></label>' +
    '<div class="row wide"><button class="primary" type="submit"' + (S.busy ? " disabled" : "") + ">" + t_("Sign in") + '</button><button class="mini-btn" type="button" id="acct-resend">' + t_("Send a new code") + '</button><button class="mini-btn" type="button" id="acct-back">' + t_("Use another email") + "</button></div>" +
    '<p class="note wide" id="acct-msg">' + esc(S.msg || t_("You can also open the link in the email on this device.")) + "</p></form></div>";
  return '<div class="acct-card">' + intro +
    '<form class="jform" id="acct-email-form"><label class="wide">' + t_("Email") + '<input id="acct-email" type="email" autocomplete="email" inputmode="email" maxlength="254" required value="' + esc(S.email) + '" placeholder="you@example.com"></label>' +
    // the Terms come up once, only when the email has no account yet
    (S.isNew ? '<label class="wide acct-agree"><input id="acct-terms" type="checkbox" required' + (S.agreed ? " checked" : "") + "><span>" +
      t_("New here: I am 18 or older and accept the {terms}. See the {privacy}.", { terms: link("/terms", t_("Terms of Use")), privacy: link("/privacy", t_("privacy policy")) }) + "</span></label>" : "") +
    '<div class="row wide"><button class="primary" type="submit"' + (S.busy ? " disabled" : "") + ">" + (S.isNew ? t_("Create my account") : t_("Send me a code")) + "</button></div>" +
    '<p class="note wide" id="acct-msg">' + (S.msg ? esc(S.msg) : t_("No password: we email you a code.")) + "</p></form></div>";
}

function signedIn() {
  const p = S.profile || {}, c = counts();
  S.fav = S.fav || [...(p.favourite_places || [])];
  const favs = S.fav.map((id) => O.placeOf(id)).filter(Boolean);
  return '<div class="acct-card"><div class="acct-who"><span class="acct-av">' + esc(initial()) + "</span><div><b>" + esc(p.display_name || t_("Your profile")) + "</b><span>" + esc(S.user.email) + "</span></div>" +
    (S.founding ? '<span class="badge-f">' + (S.founding.founding ? t_("Founding Member · spot {n}", { n: S.founding.spot }) : t_("On the list")) + "</span>" : "") + "</div>" +
    (S.founding ? "" : '<div class="fm-reserve"><div><b>' + t_("Become a Founding Member") + "</b><span>" +
      t_("Membership opens soon. Reserve your spot with this account: CHF 19 for the first year, then CHF 39, nothing to pay now. We email you when it opens.") +
      '</span></div><button class="primary" id="acct-founding">' + t_("Reserve my spot") + "</button></div>") +
    '<div class="row"><span class="acct-sync' + (S.sync === "error" ? " err" : "") + '" id="acct-sync">' + esc(syncText()) + '</span><button class="mini-btn" id="acct-syncnow">' + t_("Sync now") + "</button>" +
    '<button class="mini-btn" id="acct-out">' + t_("Sign out") + "</button></div></div>" +
    '<div><h3>' + t_("Profile") + '</h3><form class="jform acct-card" id="acct-profile" autocomplete="off">' +
    '<label>' + t_("Name") + '<input id="pf-name" maxlength="60" value="' + esc(p.display_name || "") + '" placeholder="' + esc(t_("How you want to be called")) + '"></label>' +
    '<label>' + t_("I am") + '<select id="pf-level">' + LEVELS.map(([v, l]) => '<option value="' + v + '"' + (v === (p.level || "") ? " selected" : "") + ">" + esc(t_(l)) + "</option>").join("") + "</select></label>" +
    '<label>' + t_("Studying or certified") + '<input id="pf-study" maxlength="60" list="pf-study-list" value="' + esc(p.studying || "") + '" placeholder="WSET Level 3"><datalist id="pf-study-list">' + STUDY.map((s) => '<option value="' + esc(s) + '">').join("") + "</datalist></label>" +
    '<label>' + t_("Where you live") + '<input id="pf-loc" maxlength="60" value="' + esc(p.location || "") + '" placeholder="Zurich, Switzerland"></label>' +
    '<label class="wide">' + t_("About you") + '<textarea id="pf-bio" maxlength="500" placeholder="' + esc(t_("What you drink, what you study, where you love to go")) + '">' + esc(p.bio || "") + "</textarea></label>" +
    '<label class="wide">' + t_("Favourite places (up to 12)") + '<div class="chips-edit" id="pf-favs">' + favs.map((f) => '<button type="button" class="mini-btn on" data-unfav="' + esc(f.id) + '">' + esc(f.name) + " ✕</button>").join("") + "</div>" +
    (S.fav.length < 12 ? '<input id="pf-fav-add" placeholder="' + esc(t_("Add a place: Musigny, Barolo, Mosel…")) + '"><ul class="sugg" id="pf-fav-sugg" hidden></ul>' : "") + "</label>" +
    '<div class="row wide"><button class="primary" type="submit">' + t_("Save profile") + '</button><span class="note" id="pf-msg"></span></div></form></div>' +
    '<div><h3>' + t_("Your data") + '</h3><div class="acct-card"><p class="lead" style="margin:0">' +
    t_("Kept in your account and on this device: {list}.", { list: countList(c) }) + "</p>" +
    '<div class="row"><button class="mini-btn" id="acct-export">' + t_("Download everything (JSON)") + "</button></div></div></div>" +
    // the two actions that cannot be undone sit folded away, and each asks again before it runs
    '<details class="acct-danger"' + (S.dangerOpen ? " open" : "") + '><summary>' + t_("Clear this device or delete the account") + '</summary><div class="acct-card">' +
    '<div><b>' + t_("Sign out and clear this device") + '</b><p class="note">' + t_("Removes your saved places, tastings, notes, recent places and compare list from this browser. Your account keeps them, and they come back when you sign in again.") + "</p>" +
    (S.confirmClear
      ? '<div class="row"><span class="note">' + t_("Clear this device now?") + '</span><button class="mini-btn warn" id="acct-out-clear">' + t_("Yes, sign out and clear") + '</button><button class="mini-btn" id="acct-clear-cancel">' + t_("Cancel") + "</button></div>"
      : '<div class="row"><button class="mini-btn" id="acct-out-clear">' + t_("Sign out and clear this device") + "</button></div>") + "</div>" +
    '<div><b>' + t_("Delete my account") + '</b><p class="note">' + t_("Deletes your profile and everything synced to your account, for good. What is on this device stays here. Download your data first if you want to keep it.") + "</p>" +
    '<label class="wide">' + t_("Type your email to confirm") + '<input id="acct-del-email" type="email" autocomplete="off" placeholder="' + esc(S.user.email) + '"></label>' +
    '<div class="row"><button class="mini-btn warn" id="acct-delete" disabled>' + t_("Delete my account for good") + "</button></div></div>" +
    "</div></details>";
}

// ---------- events
function wire() {
  const rt = $("acct-retry");
  if (rt) rt.onclick = () => { S.loadFailed = false; rerender(); };
  const ef = $("acct-email-form");
  if (ef) ef.onsubmit = async (e) => {
    e.preventDefault();
    const email = $("acct-email").value.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return msg(t_("Please enter a valid email address."));
    if (email !== S.email) S.isNew = false;
    if (S.isNew && !$("acct-terms").checked) { $("acct-terms").focus(); return msg(t_("Please confirm that you are 18 or older and accept the Terms of Use.")); }
    if (S.isNew) S.agreed = true;
    S.email = email; await sendCode();
  };
  const cf = $("acct-code-form");
  if (cf) {
    $("acct-code").focus();
    cf.onsubmit = async (e) => {
      e.preventDefault();
      const token = $("acct-code").value.replace(/\D/g, "");
      if (token.length < 6) return msg(t_("Enter the code from the email."));
      busy(true);
      const { error } = await S.sb.auth.verifyOtp({ email: S.email, token, type: "email" });
      busy(false);
      if (error) return msg(/expired|invalid/i.test(error.message) ? t_("That code is wrong or has expired. Ask for a new one.") : t_("Could not sign in. Please try again."));
      O.toast(t_("Signed in. Your atlas is syncing."));
    };
    $("acct-resend").onclick = sendCode;
    $("acct-back").onclick = () => { S.step = "email"; S.msg = ""; S.isNew = false; rerender(); };
  }
  if (!S.user) return;
  $("acct-syncnow").onclick = () => fullSync();
  const fr = $("acct-founding");
  if (fr) fr.onclick = async () => {
    fr.disabled = true;
    const { data, error } = await S.sb.rpc("founding_reserve", { p_consent_version: "2026-10-21", p_source: "account", p_lang: (navigator.language || "").slice(0, 12) });
    if (error) { fr.disabled = false; return O.toast(t_("Could not reserve the spot. Please try again.")); }
    S.founding = Array.isArray(data) ? data[0] : data;
    rerender();
    O.toast(S.founding?.founding ? t_("Founding spot {n} is yours.", { n: S.founding.spot }) : t_("You are on the list."));
  };
  $("acct-out").onclick = () => signOut(false);
  const dz = document.querySelector(".acct-danger");
  if (dz) dz.ontoggle = () => { S.dangerOpen = dz.open; };
  $("acct-out-clear").onclick = () => {
    if (!S.confirmClear) { S.confirmClear = true; S.dangerOpen = true; rerender(); return; }
    S.confirmClear = false; signOut(true);
  };
  const cc = $("acct-clear-cancel");
  if (cc) cc.onclick = () => { S.confirmClear = false; rerender(); };
  $("acct-export").onclick = () => {
    const blob = new Blob([JSON.stringify({ app: "Open Wine Atlas", exported: new Date().toISOString(), profile: S.profile, saved: MY.saved, journal: MY.journal, notes: MY.notes }, null, 1)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "open-wine-atlas.json"; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  };
  const del = $("acct-delete"), delEmail = $("acct-del-email");
  delEmail.oninput = () => { del.disabled = delEmail.value.trim().toLowerCase() !== String(S.user.email).toLowerCase(); };
  del.onclick = async () => {
    if (delEmail.value.trim().toLowerCase() !== String(S.user.email).toLowerCase()) return;
    del.disabled = true;
    const { error } = await S.sb.rpc("delete_my_account");
    if (error) { del.disabled = false; return O.toast(t_("Could not delete the account. Please try again.")); }
    await S.sb.auth.signOut({ scope: "local" }).catch(() => {});
    clearMeta(); S.user = null; S.profile = null; S.founding = null; stopPolling(); rerender();
    O.toast(t_("Your account is deleted. Your atlas stays on this device."));
  };
  const pf = $("acct-profile");
  pf.onsubmit = async (e) => {
    e.preventDefault();
    const row = { display_name: $("pf-name").value.trim() || null, level: $("pf-level").value || null, studying: $("pf-study").value.trim() || null,
      location: $("pf-loc").value.trim() || null, bio: $("pf-bio").value.trim() || null, favourite_places: S.fav.slice(0, 12) };
    $("pf-msg").textContent = t_("Saving…");
    const { error } = await S.sb.from("profiles").update(row).eq("id", S.user.id);
    if (error) { $("pf-msg").textContent = t_("Could not save. Please try again."); return; }
    S.profile = { ...S.profile, ...row }; rerender(); O.toast(t_("Profile saved."));
  };
  document.querySelectorAll("[data-unfav]").forEach((b) => b.onclick = () => { S.fav = S.fav.filter((x) => x !== b.dataset.unfav); keepFormAndRender(); });
  const inp = $("pf-fav-add"), sg = $("pf-fav-sugg");
  if (inp) {
    let opts = [];
    inp.addEventListener("input", () => {
      opts = inp.value.trim() ? O.search(inp.value).filter((r) => !S.fav.includes(r[1])).slice(0, 8) : [];
      sg.innerHTML = opts.map((r, i) => '<li><button type="button" data-i="' + i + '">' + esc(r[0]) + "<small>" + esc(O.kindOf({ rank: r[4], level: r[3], country: r[2] }) + " · " + r[2]) + "</small></button></li>").join("");
      sg.hidden = !opts.length;
    });
    sg.addEventListener("click", (e) => { const b = e.target.closest("button[data-i]"); if (!b) return; S.fav.push(opts[+b.dataset.i][1]); keepFormAndRender(); $("pf-fav-add")?.focus(); });
  }
}
// re-render the account view without losing what is typed in the profile form
function keepFormAndRender() {
  const keep = ["pf-name", "pf-level", "pf-study", "pf-loc", "pf-bio"].map((id) => [id, $(id)?.value]);
  O.renderDash();
  keep.forEach(([id, v]) => { if ($(id) && v != null) $(id).value = v; });
}
function msg(t) { S.msg = t; const el = $("acct-msg"); if (el) el.textContent = t; }
function busy(b) { S.busy = b; document.querySelectorAll(".acct button[type=submit]").forEach((x) => { x.disabled = b; }); }
async function sendCode() {
  busy(true);
  const create = !!(S.isNew && S.agreed);
  const options = { shouldCreateUser: create, emailRedirectTo: location.origin + "/?signin=1" };
  if (create) options.data = { terms_version: TERMS_VERSION, terms_accepted_at: new Date().toISOString(), adult_confirmed: true };
  const { error } = await S.sb.auth.signInWithOtp({ email: S.email, options });
  busy(false);
  if (error && (error.code === "otp_disabled" || /signups not allowed/i.test(error.message))) {
    // no account with this email yet: ask for the Terms once, then the same button creates it
    S.isNew = true; S.msg = t_("Welcome. Tick the box to create your free account."); return rerender();
  }
  if (error) {
    S.msg = /rate|seconds|too many/i.test(error.message) ? t_("Please wait a minute before asking for another code.") : t_("Could not send the code. Please try again.");
    return S.step === "code" ? msg(S.msg) : rerender();
  }
  S.step = "code"; S.msg = ""; rerender();
}
async function signOut(clear) {
  stopPolling();
  if (!clear && S.syncing) await new Promise((ok) => setTimeout(ok, 800));
  await S.sb.auth.signOut({ scope: "local" }).catch(() => {});
  clearMeta(); S.user = null; S.profile = null; S.founding = null; S.fav = null; S.sync = "idle"; S.confirmClear = false; S.dangerOpen = false;
  if (clear) { MY.saved = {}; MY.journal = []; MY.notes = []; MY.recent = []; MY.compare = []; O.myChanged(["saved", "journal", "notes", "recent", "compare"]); }
  rerender();
  O.toast(clear ? t_("Signed out. This device is cleared.") : t_("Signed out. Your atlas stays on this device."));
}

window.OWA_ACCOUNT = { render, wire, line, sync: fullSync, signedIn: () => !!S.user };

// ---------- boot: restore a session only when there is one (or a sign-in link was just opened)
const url = new URL(location.href);
let hasSession = false;
try { hasSession = !!localStorage.getItem(AUTH_KEY); } catch (e) {}
if (hasSession || url.searchParams.has("code")) {
  client().catch((e) => {
    if (e.message !== "not_configured") console.error(e);
    if (url.searchParams.has("code")) O.toast(t_("Sign-in could not finish here. Type the code from the email instead."));
  });
}
// until accounts open (OWA_CONFIG.accountsOpen), no sign-in prompt on the overview
if (!window.OWA_CONFIG) loadScript("/config.js").then(() => { if (!window.OWA_CONFIG?.accountsOpen) { S.unavailable = true; rerender(); } }).catch(() => {});
else if (!window.OWA_CONFIG.accountsOpen) S.unavailable = true;
rerender();
})();
