// Open Wine Atlas: Wine Passport and members' tasting notes (web only).
//
// A Passport is the public page of a member who chose to show it (openwineatlas.com/u/<handle>): who they are, what
// they study, their badges, the origins they have tasted on the map, and the tasting notes they chose to share.
// Under every place, the notes members shared about wines from it. Everything is read through two database functions
// (passport, place_tastings, see supabase/migrations/…_passport.sql) that apply privacy and moderation first.
// A note shows the town it was tasted in, never a precise position. Any visitor can report a note or a Passport.
(() => {
"use strict";
const O = window.OWA;
if (!O || window.OWA_PASSPORT) return;
const { esc, t_, cname } = O;
const $ = (id) => document.getElementById(id);
const N_ = (x) => x;
const GOLD = "#e7c06a", PARCH = "#e6dccb";

// ---------- the database, read with the public key (no account needed)
async function cfg() {
  if (!window.OWA_CONFIG) await new Promise((ok) => { const s = document.createElement("script"); s.src = "/config.js"; s.onload = ok; s.onerror = ok; document.head.appendChild(s); });
  return window.OWA_CONFIG && window.OWA_CONFIG.accountsOpen ? window.OWA_CONFIG : null;
}
async function rpc(name, args) {
  const C = await cfg(); if (!C) throw new Error("not_configured");
  const r = await fetch(C.supabaseUrl + "/rest/v1/rpc/" + name, { method: "POST",
    headers: { apikey: C.supabaseKey, "Content-Type": "application/json" }, body: JSON.stringify(args) });
  if (!r.ok) throw new Error(name + " " + r.status);
  const txt = await r.text();
  return txt ? JSON.parse(txt) : null;
}

const LEVELS = { student: N_("Wine student"), sommelier: N_("Sommelier"), enthusiast: N_("Wine lover"), trade: N_("Wine trade"), winemaker: N_("Winemaker"), other: N_("Other") };
const whereTxt = (n) => [n.venue, n.city].filter(Boolean).join(", ");
const fmtDate = (d) => { try { return new Date(d + "T12:00:00").toLocaleDateString(O.LOCALE, { day: "numeric", month: "short", year: "numeric" }); } catch (e) { return d; } };

// one tasting note, as a card
function noteCard(n, opts = {}) {
  const title = [n.wine, n.vintage].filter(Boolean).join(" ") || n.place || "";
  const where = whereTxt(n);
  return '<div class="pp-note">' +
    '<div class="pp-note-top">' + (n.score ? '<span class="sc">' + esc(n.score) + "</span>" : "") + "<b>" + esc(title) + "</b></div>" +
    '<div class="pp-note-meta">' +
      (n.place_id && !opts.noPlace ? '<button class="pp-origin" data-goto="' + esc(n.place_id) + '">' + esc(n.place) + "</button>" : "") +
      (where ? "<span>" + esc(t_("Tasted at {where}", { where })) + "</span>" : "") +
      (n.date ? "<span>" + esc(fmtDate(n.date)) + "</span>" : "") + "</div>" +
    (n.note ? "<p>" + esc(n.note) + "</p>" : "") +
    '<div class="pp-note-foot">' +
      (opts.byline && n.handle ? '<button class="pp-by" data-passport="' + esc(n.handle) + '">' + esc(n.name || "@" + n.handle) + "</button>" : "<span></span>") +
      '<button class="pp-report" data-report="tasting" data-h="' + esc(n.handle) + '" data-i="' + esc(n.id) + '">' + t_("Report") + "</button></div></div>";
}

// ---------- the Passport, in the side panel, with its map
let SHOWN = null;
async function open(handle) {
  handle = String(handle || "").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  if (!handle) return;
  const head = $("sh-head"), body = $("sh-body");
  O.closeDash && O.closeDash();
  head.innerHTML = '<div class="eyebrow"><span>' + t_("Wine Passport") + "</span></div><h2>@" + esc(handle) + "</h2>";
  body.innerHTML = '<p class="lede">' + t_("Loading…") + "</p>";
  $("sheet").classList.add("open");
  let P = null;
  try { P = await rpc("passport", { p_handle: handle }); } catch (e) { console.warn(e); }
  if (!P) {
    body.innerHTML = '<p class="lede">' + t_("This Passport is private or does not exist.") + "</p>";
    clearMap(); return;
  }
  SHOWN = P;
  const notes = P.tastings || [];
  const origins = new Map(); notes.forEach((n) => { if (n.place_id && !origins.has(n.place_id)) origins.set(n.place_id, n); });
  const countries = new Set(notes.map((n) => n.country).filter(Boolean));
  const towns = new Set(notes.map((n) => n.city).filter(Boolean));
  const lessons = (P.lessons || []).length;
  const role = [P.level && t_(LEVELS[P.level] || P.level), P.studying].filter(Boolean).join(" · ");
  head.innerHTML = '<div class="eyebrow"><span>' + t_("Wine Passport") + "</span><span>·</span><span>@" + esc(P.handle) + "</span></div>" +
    "<h2>" + esc(P.name || "@" + P.handle) + "</h2>" +
    '<div class="crumbs">' + esc([role, P.location].filter(Boolean).join(" · ")) + "</div>";
  const badges = [];
  if (P.founding) badges.push('<span class="pp-badge gold">' + t_("Founding Member · No. {n}", { n: P.founding }) + "</span>");
  if (P.studying) badges.push('<span class="pp-badge">' + esc(P.studying) + "</span>");
  if (lessons >= 1) badges.push('<span class="pp-badge">' + t_("{n} lessons completed", { n: lessons }) + "</span>");
  if (countries.size >= 5) badges.push('<span class="pp-badge">' + t_("Origins from {n} countries", { n: countries.size }) + "</span>");
  let html = "";
  if (P.bio) html += '<p class="lede">' + esc(P.bio) + "</p>";
  if (badges.length) html += '<div class="pp-badges">' + badges.join("") + "</div>";
  const tiles = [[notes.length, t_("tasting notes")], [origins.size, t_("origins tasted")], [countries.size, t_("countries")], [lessons, t_("lessons completed")]];
  html += '<div class="gtiles n4">' + tiles.map(([v, l]) => "<div><b>" + esc(v) + "</b><span>" + esc(l) + "</span></div>").join("") + "</div>";
  if (origins.size) html += '<div class="sec"><h3>' + t_("Origins tasted · {n}", { n: origins.size }) + '</h3><div class="chips">' +
    [...origins.values()].map((n) => '<button data-goto="' + esc(n.place_id) + '">' + esc(n.place) + "</button>").join("") + "</div>" +
    (towns.size ? '<p class="pp-legend"><i class="o"></i>' + t_("origin of the wine") + ' <i class="t"></i>' + t_("town where it was tasted") + "</p>" : "") + "</div>";
  const favs = (P.favourites || []).map((id) => O.placeOf(id)).filter(Boolean);
  if (favs.length) html += '<div class="sec"><h3>' + t_("Favourite places") + '</h3><div class="chips">' + favs.map((f) => '<button data-goto="' + esc(f.id) + '">' + esc(f.name) + "</button>").join("") + "</div></div>";
  html += '<div class="sec"><h3>' + t_("Tasting notes · {n}", { n: notes.length }) + "</h3>" +
    (notes.length ? '<div class="pp-notes">' + notes.map((n) => noteCard(n)).join("") + "</div>" : '<p class="pp-empty">' + t_("No shared tasting notes yet.") + "</p>") + "</div>";
  html += '<div class="sec pp-actions"><button class="primary" data-pp-share="' + esc(P.handle) + '">' + t_("Share this Passport") + "</button>" +
    (mine(P.handle) ? "" : '<button class="pp-report" data-report="profile" data-h="' + esc(P.handle) + '">' + t_("Report this Passport") + "</button>") + "</div>";
  html += '<div class="source">' + t_("Member since {date}. Tasting notes are the member's own and are shown as written. Towns from GeoNames.", { date: fmtDate(P.since) }) + "</div>";
  body.innerHTML = html; body.scrollTop = 0;
  drawMap(notes);
}
const mine = (h) => { const A = window.OWA_ACCOUNT, p = A && A.profile && A.profile(); return !!(p && p.handle === h); };

// the map: origins in gold, towns in parchment, a fine line from where it was tasted to where it comes from
function drawMap(notes) {
  const map = O.map; if (!map) return;
  const feats = [], seen = new Set(), pts = [];
  notes.forEach((n) => {
    const r = n.place_id && O.recOf(n.place_id);
    const o = n.lat != null ? [n.lon, n.lat] : r ? [(r[6][0] + r[6][2]) / 2, (r[6][1] + r[6][3]) / 2] : null;
    const t = n.city_lat != null ? [n.city_lon, n.city_lat] : null;
    if (o && !seen.has("o" + n.place_id)) { seen.add("o" + n.place_id); feats.push({ type: "Feature", properties: { k: "o", name: n.place || "" }, geometry: { type: "Point", coordinates: o } }); pts.push(o); }
    if (t && !seen.has("t" + n.city + t)) { seen.add("t" + n.city + t); feats.push({ type: "Feature", properties: { k: "t", name: n.city || "" }, geometry: { type: "Point", coordinates: t } }); pts.push(t); }
    if (o && t) feats.push({ type: "Feature", properties: { k: "l" }, geometry: { type: "LineString", coordinates: [t, o] } });
  });
  const data = { type: "FeatureCollection", features: feats };
  if (!map.getSource("passport")) {
    map.addSource("passport", { type: "geojson", data });
    map.addLayer({ id: "pp-lines", type: "line", source: "passport", filter: ["==", ["get", "k"], "l"],
      paint: { "line-color": GOLD, "line-opacity": 0.55, "line-width": 1.2, "line-dasharray": [2, 2] } });
    map.addLayer({ id: "pp-towns", type: "circle", source: "passport", filter: ["==", ["get", "k"], "t"],
      paint: { "circle-radius": 4, "circle-color": PARCH, "circle-stroke-color": "#0b0b0d", "circle-stroke-width": 1.5 } });
    map.addLayer({ id: "pp-origins", type: "circle", source: "passport", filter: ["==", ["get", "k"], "o"],
      paint: { "circle-radius": 6, "circle-color": GOLD, "circle-stroke-color": "#0b0b0d", "circle-stroke-width": 1.5 } });
    map.addLayer({ id: "pp-labels", type: "symbol", source: "passport", filter: ["!=", ["get", "k"], "l"],
      layout: { "text-field": ["get", "name"], "text-font": ["noto-medium"], "text-size": 11.5, "text-offset": [0, 1.1], "text-anchor": "top", "text-optional": true },
      paint: { "text-color": ["case", ["==", ["get", "k"], "o"], GOLD, PARCH], "text-halo-color": "rgba(11,11,13,.92)", "text-halo-width": 1.4 } });
  } else map.getSource("passport").setData(data);
  if (pts.length) {
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    // the atlas' own framing, which leaves room for the rail and this panel; a margin so the dots do not touch the edge
    const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys), m = Math.max(0.6, Math.max(w, h) * 0.12);
    try { O.fitTo([Math.min(...xs) - m, Math.min(...ys) - m, Math.max(...xs) + m, Math.max(...ys) + m]); } catch (e) { console.warn(e); }
  }
}
function clearMap() { const s = O.map && O.map.getSource("passport"); if (s) s.setData({ type: "FeatureCollection", features: [] }); SHOWN = null; }
// the panel closed or shows something else: the Passport leaves the map
new MutationObserver(() => { if (SHOWN && !$("sheet").classList.contains("open")) clearMap(); }).observe($("sheet"), { attributes: true, attributeFilter: ["class"] });

// ---------- under a place: the notes members shared about wines from it
async function placeNotes(p, token, isCurrent) {
  let list = [];
  try { list = await rpc("place_tastings", { p_place: p.id, p_limit: 20 }); } catch (e) { return; }
  if (!isCurrent(token) || !Array.isArray(list)) return;
  const body = $("sh-body"); if (!body || body.querySelector(".deep-wall")) return;
  const old = body.querySelector("#pp-place"); if (old) old.remove();
  const sec = document.createElement("div");
  sec.className = "sec"; sec.id = "pp-place";
  sec.innerHTML = "<h3>" + t_("Tasting notes from members · {n}", { n: list.length }) + "</h3>" +
    (list.length ? '<div class="pp-notes">' + list.map((n) => noteCard(n, { byline: true, noPlace: true })).join("") + "</div>"
      : '<p class="pp-empty">' + t_("No member has shared a tasting note on a wine from here yet.") + "</p>") +
    '<p class="pp-cta"><button class="mini-btn" data-taste-here="' + esc(p.id) + '">' + t_("Log a tasting note from here") + "</button></p>";
  const src = body.querySelector(".source");
  if (src) body.insertBefore(sec, src); else body.appendChild(sec);
}

// ---------- reporting
function report(kind, handle, item) {
  const box = document.createElement("div");
  box.className = "onb"; box.setAttribute("role", "dialog"); box.setAttribute("aria-modal", "true");
  box.innerHTML = '<div class="onb-card"><span class="ey">' + t_("Report") + "</span><h3>" + (kind === "tasting" ? t_("Report this tasting note") : t_("Report this Passport")) + "</h3>" +
    '<p class="onb-lead">' + t_("Tell us what is wrong. The atlas team reviews every report and removes what breaks the Terms of Use.") + "</p>" +
    '<label class="onb-lab">' + t_("Reason (optional)") + '<textarea id="rp-why" maxlength="500" rows="3"></textarea></label>' +
    '<div class="onb-acts"><button type="button" class="onb-skip" data-rp="cancel">' + t_("Cancel") + '</button><button type="button" class="primary" data-rp="send">' + t_("Send report") + "</button></div></div>";
  document.body.appendChild(box);
  box.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-rp]"); if (!b) { if (e.target === box) box.remove(); return; }
    if (b.dataset.rp === "cancel") return box.remove();
    b.disabled = true;
    try { await rpc("report_content", { p_kind: kind, p_handle: handle, p_item: item || null, p_reason: $("rp-why").value.trim() || null }); O.toast(t_("Thank you. The report is with the atlas team.")); }
    catch (err) { O.toast(t_("Could not send the report. Please try again.")); }
    box.remove();
  });
}

document.addEventListener("click", (e) => {
  const pp = e.target.closest("[data-passport]");
  if (pp) { e.preventDefault(); open(pp.dataset.passport); try { history.replaceState(null, "", "/?u=" + encodeURIComponent(pp.dataset.passport)); } catch (er) {} return; }
  const rp = e.target.closest("[data-report]");
  if (rp) { e.preventDefault(); report(rp.dataset.report, rp.dataset.h, rp.dataset.i); return; }
  const sh = e.target.closest("[data-pp-share]");
  if (sh) {
    e.preventDefault();
    const A = window.OWA_ACCOUNT, h = sh.dataset.ppShare, url = location.origin + "/u/" + h;
    if (A && A.sharePassport) return A.sharePassport(h, SHOWN && SHOWN.name);
    if (navigator.share) navigator.share({ url }).catch(() => {}); else navigator.clipboard.writeText(url).then(() => O.toast(t_("Link copied.")));
    return;
  }
  const th = e.target.closest("[data-taste-here]");
  if (th) { e.preventDefault(); O.openDash("journal", th.dataset.tasteHere); }
});

window.OWA_PASSPORT = { open, placeNotes, report };
})();
