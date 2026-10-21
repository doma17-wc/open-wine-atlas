// Open Wine Atlas: study and quiz (web only).
//
// Paths of lessons (web/data/study.json, written by people, checked against the atlas) and quizzes:
//   lesson quiz    the questions written for a lesson
//   region drill   questions built from the atlas data of a region: where it is, its grape, its rank, its parent,
//                  which lies highest, its state or commune
//   map quiz       only the map questions: name the outlined place, or find a place on the map
//   review         spaced repetition: every question answered becomes a card; a miss comes back tomorrow,
//                  a right answer later and later (Leitner boxes)
// Free: the first lesson of each path and FREE_PER_DAY answers a day. Members: everything.
// Progress lives in My atlas (MY.study) and syncs with the account like the rest of it.
(() => {
"use strict";
const O = window.OWA;
if (!O || window.OWA_STUDY) return;
const { MY, esc, t_, store } = O;
// Path levels come from web/data/study.json; listed here so pipeline/i18n_extract.py keeps their translations.
const N_ = (x) => x;
const LEVELS = [N_("Intermediate"), N_("Advanced")];
const $ = (id) => document.getElementById(id);
const FREE_PER_DAY = 10;
const BOX_DAYS = [0, 1, 3, 7, 16, 35];
const SESSION = 10;

// ---------- state
function blank() { return { cards: {}, done: {}, stats: { answered: 0, right: 0, days: [] }, today: { d: "", n: 0 } }; }
function loadState() {
  let s = null;
  try { s = JSON.parse(store.get("study") || "null"); } catch (e) {}
  const b = blank();
  if (!s || typeof s !== "object") return b;
  return { cards: s.cards || {}, done: s.done || {}, stats: Object.assign(b.stats, s.stats || {}), today: Object.assign(b.today, s.today || {}) };
}
// MY.study can be replaced by a sync from another device: fill in whatever is missing each time
function norm(s) {
  const b = blank();
  if (!s || typeof s !== "object") return b;
  return { cards: s.cards || {}, done: s.done || {}, stats: Object.assign(b.stats, s.stats || {}), today: Object.assign(b.today, s.today || {}) };
}
MY.study = norm(MY.study && Object.keys(MY.study).length ? MY.study : loadState());
const ST = () => { const s = MY.study; if (!s || !s.cards || !s.done || !s.stats || !s.today) MY.study = norm(s); return MY.study; };
const save = () => O.saveMY("study");
const dayStr = (t = Date.now()) => { const d = new Date(t); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const member = () => !!(window.OWA_ACCOUNT && window.OWA_ACCOUNT.member && window.OWA_ACCOUNT.member()) || store.get("member") === "1";
function usedToday() { const t = ST().today; return t.d === dayStr() ? t.n : 0; }
const leftToday = () => member() ? Infinity : Math.max(0, FREE_PER_DAY - usedToday());
function countAnswer(key, ok) {
  const s = ST(), today = dayStr();
  if (s.today.d !== today) s.today = { d: today, n: 0 };
  s.today.n++;
  s.stats.answered++; if (ok) s.stats.right++;
  if (s.stats.days[s.stats.days.length - 1] !== today) { s.stats.days.push(today); if (s.stats.days.length > 400) s.stats.days = s.stats.days.slice(-400); }
  if (!key) { save(); return; } // a question made up on the spot (a data game): no review card
  const c = s.cards[key] || { b: 0, n: 0, ok: 0 };
  c.n++; if (ok) c.ok++;
  c.b = ok ? Math.min(BOX_DAYS.length - 1, c.b + 1) : 1;
  c.due = ok ? Date.now() + BOX_DAYS[c.b] * 864e5 : Date.now() + 864e5 * (c.n > 1 ? 1 : 0.0001);
  c.last = Date.now();
  s.cards[key] = c;
  save();
}
function streak() {
  const days = new Set(ST().stats.days);
  let n = 0, t = Date.now();
  if (!days.has(dayStr(t))) t -= 864e5;
  while (days.has(dayStr(t))) { n++; t -= 864e5; }
  return n;
}
const dueKeys = () => Object.entries(ST().cards).filter(([, c]) => c.due <= Date.now()).sort((a, b) => a[1].due - b[1].due).map(([k]) => k);

// ---------- content
let DATA = null, loading = null;
function loadData() {
  if (DATA) return Promise.resolve(DATA);
  if (!loading) loading = fetch("/data/study.json").then((r) => r.json()).then((d) => {
    DATA = d;
    DATA.byLesson = new Map(); DATA.byPath = new Map();
    d.paths.forEach((p) => { DATA.byPath.set(p.id, p); p.lessons.forEach((l, i) => { l.path = p; l.n = i; DATA.byLesson.set(l.id, l); }); });
    return DATA;
  }).catch((e) => { loading = null; throw e; });
  return loading;
}
const lessonFree = (l) => l.n === 0 || member();

// ---------- places of a scope (tree keys), with their details
// how much two boxes share, as a part of the smaller one
const overlap = (a, b) => {
  const w = Math.min(a[2], b[2]) - Math.max(a[0], b[0]), h = Math.min(a[3], b[3]) - Math.max(a[1], b[1]);
  if (w <= 0 || h <= 0) return 0;
  return (w * h) / Math.max(1e-12, Math.min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1])));
};
const isArea = (r) => r && r[6] && !(r[6][0] === r[6][2] && r[6][1] === r[6][3]);
function placesIn(keys) {
  const out = [], seen = new Set();
  const walk = (k, d) => {
    if (seen.has(k) || d > 8) return; seen.add(k);
    const r = O.byId.get(k); if (r) out.push(r);
    (O.kidsOf(k) || []).forEach((c) => walk(c, d + 1));
  };
  keys.forEach((k) => walk(k, 0));
  return out;
}
const DET = new Map();
async function detailsFor(recs) {
  const ccs = [...new Set(recs.map((r) => r[2]))];
  await Promise.all(ccs.map((cc) => O.getDetails(cc).then((d) => { Object.entries(d || {}).forEach(([k, v]) => DET.set(k, v)); }).catch(() => {})));
}
const det = (id) => DET.get(id) || {};
const nameOf = (k) => { const n = O.tnode(k); return (n && n[0]) || (O.byId.get(k) || [k])[0]; };
// a German single vineyard shares its name with many others: say whose it is ("Sonnenuhr (Wehlen)")
const nm = (r) => r[2] === "DE" && r[3] === "vineyard" && r[7] ? r[0] + " (" + r[7].split(", ")[0] + ")" : r[0];
// communes come from the registers in plain letters (Vosne-Romanee): use the accented village name when the atlas has it
let PLAIN_NAMES = null;
function prettyCommune(c) {
  if (!PLAIN_NAMES) { PLAIN_NAMES = new Map(); O.INDEX.forEach((r) => { if (r[2] !== "FR" || r[4] || /\bcru\b/i.test(r[0])) return; const k = plain(r[0]); if (!PLAIN_NAMES.has(k)) PLAIN_NAMES.set(k, r[0]); }); }
  return PLAIN_NAMES.get(plain(c)) || c.replace(/-(Les|La|Le|Sur|En|Sous|Lès|De|Du|Des)-/g, (m) => m.toLowerCase());
}
const US_STATE = (abbr) => /^[A-Z]{2}$/.test(abbr) ? nameOf("g:US/" + abbr) : abbr;
// where a place lies, for the explanations: its parent in the tree, or for an AVA its states
function lies(r) {
  const d = det(r[1]);
  if (r[2] === "US" && d.states && d.states.length) return t_("{name} lies in {parent}.", { name: r[0], parent: d.states.map(US_STATE).join(", ") });
  const par = parentKey(r[1]);
  return par && !/^g:[A-Z]{2}$/.test(par) ? t_("{name} lies in {parent}.", { name: nm(r), parent: nameOf(par) }) : "";
}
const parentKey = (id) => { const p = O.pathOf(id); return p.length > 1 ? p[p.length - 2] : null; };
const shuffle = (a) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const pick1 = (a) => a[Math.floor(Math.random() * a.length)];
// a question with the right answer at a random position among distinct options
function mc(key, q, right, wrong, extra = {}) {
  const others = shuffle([...new Set(wrong.filter((w) => w && w !== right))]).slice(0, 3);
  if (others.length < (extra.min || 3)) return null;
  const options = shuffle([right, ...others]);
  return Object.assign({ key, kind: "mc", q, options, answer: options.indexOf(right) }, extra);
}
// for "is the answer already in the name?": no accents, no case, no hyphens
const plain = (x) => String(x || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[-'’]/g, " ").replace(/\s+(premier|grand) cru\b.*$/, "").trim();
const givesAway = (name, ans) => { const a = plain(ans); return a.length > 2 && plain(name).includes(a); };
const grapeName = (g) => String(g).replace(/\s+(N|B|G|Rs|Rg)$/, "").trim();
function mainGrapes(d) {
  const w = Array.isArray(d.wines) ? d.wines : [];
  const set = [...new Set(w.flatMap((x) => x.main || []).map(grapeName))];
  if (set.length) return set;
  if (d.grapes && !/\//.test(d.grapes)) return [grapeName(d.grapes)];
  return [];
}

// ---------- question builders from the atlas data: (name, rec, pool) -> question or null
const GEN = {
  identify(r, pool) {
    if (!isArea(r)) return null;
    const par = parentKey(r[1]);
    // options whose outline covers much the same ground (Corton and Corton-Charlemagne) would make two answers right
    const apart = (x) => isArea(x) && overlap(x[6], r[6]) < 0.5;
    let sib = par ? (O.kidsOf(par) || []).map((k) => O.byId.get(k)).filter((x) => x && x[1] !== r[1] && apart(x)) : [];
    if (sib.length < 3) sib = pool.filter((x) => x[1] !== r[1] && x[3] === r[3] && apart(x));
    const q = mc("g:identify:" + r[1], t_("Which place is outlined on the map?"), nm(r), sib.map(nm), { map: "identify", place: r[1] });
    if (q) q.explain = lies(r);
    return q;
  },
  find(r) {
    if (!isArea(r)) return null;
    const par = parentKey(r[1]);
    return { key: "g:find:" + r[1], kind: "find", q: t_("Find {name} on the map.", { name: nm(r) }), place: r[1], map: "find", frame: par, explain: lies(r) };
  },
  grape(r, pool) {
    const g = mainGrapes(det(r[1]));
    if (!g.length || g.length > 2) return null;
    const right = g.join(" and ");
    const wrong = pool.map((x) => mainGrapes(det(x[1]))).filter((x) => x.length && x.length <= 2 && !x.some((y) => g.includes(y))).map((x) => x.join(" and "));
    const q = mc("g:grape:" + r[1], t_("What is the main grape of {name}?", { name: r[0] }), right, wrong, { place: r[1] });
    if (q) q.explain = t_("The rules of {name} are built on {grape}.", { name: r[0], grape: right });
    return q;
  },
  rank(r) {
    const cc = r[2];
    if (cc === "FR" && (r[4] === "grand_cru" || r[4] === "premier_cru")) {
      const right = O.RANK_LABEL[r[4]];
      const q = mc("g:rank:" + r[1], t_("How is {name} classified?", { name: r[0] }), right, ["Grand cru", "Premier cru", t_("Village appellation"), t_("Regional appellation")], { place: r[1] });
      if (q) q.explain = t_("{name} is a {rank}.", { name: r[0], rank: right.toLowerCase() });
      return q;
    }
    if (cc === "IT" && r[3] === "appellation") {
      const right = r[4] === "docg" ? "DOCG" : "DOC";
      const q = mc("g:rank:" + r[1], t_("What is the status of {name}?", { name: r[0] }), right, ["DOCG", "DOC", "IGT", "Vino"], { place: r[1] });
      if (q) q.explain = t_("{name} is a {rank}.", { name: r[0], rank: right });
      return q;
    }
    return null;
  },
  parent(r, pool) {
    const par = parentKey(r[1]);
    // grands crus that cross village lines sit under one village in the atlas tree: no question there
    if (!par || /^g:[A-Z]{2}$/.test(par) || (r[2] === "FR" && r[4] === "grand_cru") || (det(r[1]).states || []).length > 1) return null;
    const right = nameOf(par), kind = (O.tnode(par) || [])[1];
    const wrong = [...new Set(pool.map((x) => parentKey(x[1])).filter((k) => k && k !== par && !/^g:[A-Z]{2}$/.test(k) && (O.tnode(k) || [])[1] === kind))].map(nameOf);
    if (givesAway(r[0], right)) return null;
    const q = mc("g:parent:" + r[1], t_("{name} is part of…", { name: nm(r) }), right, wrong.filter((w) => w !== r[0] && !givesAway(r[0], w)), { place: r[1] });
    if (q) q.explain = t_("{name} lies in {parent}.", { name: r[0], parent: right });
    return q;
  },
  highest(r, pool) {
    const m = (x) => { const t = det(x[1]).terrain; return t && t.e ? t.e[1] : null; };
    const me = m(r);
    if (me == null) return null;
    const par = parentKey(r[1]), sib = new Set(par ? O.kidsOf(par) || [] : []);
    const cands = shuffle(pool.filter((x) => x[1] !== r[1] && sib.has(x[1]) && m(x) != null && m(x) < me - 40)).slice(0, 3);
    if (cands.length < 3) return null;
    const q = mc("g:highest:" + r[1], t_("Which of these lies highest, on average?"), nm(r), cands.map(nm), { place: r[1] });
    if (q) q.explain = [r, ...cands].map((x) => nm(x) + " " + O.fmtN(m(x)) + " m").join(" · ");
    return q;
  },
  state(r, pool) {
    if (r[2] !== "US") return null;
    const s = US_STATE((det(r[1]).states || [])[0] || "");
    if (!s || (det(r[1]).states || []).length > 1) return null;
    const wrong = [...new Set(pool.map((x) => US_STATE((det(x[1]).states || [])[0] || "")).filter(Boolean))].concat(["California", "Oregon", "Washington", "New York", "Virginia", "Texas"]);
    const q = mc("g:state:" + r[1], t_("In which state is the {name} AVA?", { name: r[0] }), s, wrong, { place: r[1] });
    if (q) q.explain = t_("{name} lies in {parent}.", { name: r[0], parent: s });
    return q;
  },
  commune(r, pool) {
    const c = det(r[1]).communes;
    if (r[2] !== "FR" || !c || c.length !== 1 || r[3] === "appellation" && !r[4] || givesAway(r[0], c[0])) return null;
    const right = prettyCommune(c[0]);
    const wrong = [...new Set(pool.map((x) => det(x[1]).communes).filter((x) => x && x.length === 1).map((x) => prettyCommune(x[0])))];
    const q = mc("g:commune:" + r[1], t_("In which commune does {name} lie?", { name: r[0] }), right, wrong, { place: r[1] });
    if (q) q.explain = t_("{name} lies in {parent}.", { name: r[0], parent: right });
    return q;
  },
};
const MAP_KINDS = ["identify", "find"], ALL_KINDS = Object.keys(GEN);

// the famous places come up more often than the hundreds of premier cru climats or Einzellagen
const WEIGHT = { grand_cru: 6, docg: 5, doca: 5, pago: 4, premier_cru: 0.6 };
const weightOf = (r) => WEIGHT[r[4]] ?? (r[3] === "vineyard" ? 0.4 : r[3] === "subzone" ? 1.5 : 4);
// the places a path's lessons talk about
function focusOf(path) {
  if (!path) return new Set();
  if (!path._focus) { path._focus = new Set(); path.lessons.forEach((l) => { l.sections.forEach((s) => (s.places || []).forEach((id) => path._focus.add(id))); l.questions.forEach((q) => q.place && path._focus.add(q.place)); }); }
  return path._focus;
}
function buildDrill(recs, kinds, n, focus = new Set()) {
  const pool = recs, cum = []; let tot = 0;
  pool.forEach((r) => { tot += weightOf(r) * (focus.has(r[1]) ? 8 : 1); cum.push(tot); });
  const pickW = () => { const x = Math.random() * tot; let lo = 0, hi = cum.length - 1; while (lo < hi) { const m = (lo + hi) >> 1; if (cum[m] < x) lo = m + 1; else hi = m; } return pool[lo]; };
  const out = [], tried = new Set();
  for (let guard = 0; out.length < n && guard < n * 40; guard++) {
    const r = pickW(), k = pick1(kinds), id = k + r[1];
    if (tried.has(id)) continue; tried.add(id);
    const q = GEN[k](r, pool);
    if (q && !out.some((x) => x.key === q.key)) out.push(q);
  }
  return out;
}
// a card key back to a question: lesson questions as written, data questions built again with fresh options
async function fromKey(key) {
  const p = key.split(":");
  if (p[0] === "l") {
    await loadData();
    const l = DATA.byLesson.get(p[1]); const q = l && l.questions.find((x) => x.id === p.slice(2).join(":"));
    return q ? lessonQ(l, q) : null;
  }
  if (["o", "x", "r"].includes(p[0])) { await loadData(); return curatedFromKey(p); }
  if (p[0] === "w") {
    await loadGameWines(); const w = GW.find((x) => x[4] === p[1]); if (!w) return null;
    const ctx = await themeCtx("region:g:" + (O.byId.get(w[2]) || [0, 0, ""])[2]); ctx.recs = ctx.pool.filter((x) => x[1] === w[2]); ctx.ids = new Set([w[2]]);
    return BUILD.where(ctx);
  }
  if (p[0] === "g" && (p[1] === "mystery" || p[1] === "pin")) {
    const id = p.slice(2).join(":"), r = O.byId.get(id); if (!r) return null;
    const par = parentKey(id), pool = placesIn([par && O.tnode(par) ? par : "g:" + r[2]]);
    await detailsFor(pool.concat([r]));
    const q = BUILD[p[1]]({ recs: [r], pool, focus: new Set(), ids: new Set([id]) });
    if (q) q.game = p[1];
    return q;
  }
  if (p[0] === "g" && GEN[p[1]]) {
    const id = p.slice(2).join(":"), r = O.byId.get(id);
    if (!r) return null;
    const par = parentKey(id), recs = placesIn([par && O.tnode(par) ? par : "g:" + r[2]]);
    await detailsFor(recs.concat([r]));
    return GEN[p[1]](r, recs);
  }
  return null;
}
const lessonQ = (l, q) => ({ key: "l:" + l.id + ":" + q.id, kind: "mc", q: q.q, options: q.options, answer: q.answer, explain: q.explain, place: q.place && O.byId.has(q.place) ? q.place : null, from: l.title });

// ---------- the quiz card over the map
let QZ = null;
function card() {
  let el = $("quiz");
  if (!el) { el = document.createElement("section"); el.id = "quiz"; el.className = "quiz"; el.setAttribute("role", "dialog"); el.setAttribute("aria-label", t_("Quiz")); document.body.appendChild(el); }
  return el;
}
async function start(title, qs, back, meta = {}) {
  if (!qs.length) { O.toast(t_("Not enough data here for a quiz yet. Try a larger region.")); return; }
  QZ = { title, qs, i: 0, right: 0, missed: [], back, answered: false, meta, pts: 0, grades: [] };
  O.closeDash();
  card().hidden = false;
  window.OWA_QUIZ_CLICK = onMapClick;
  show();
}
function stop(toStudy) {
  pinClear();
  O.quizMode(false);
  window.OWA_QUIZ_CLICK = null;
  const el = $("quiz"); if (el) el.hidden = true;
  const back = QZ && QZ.back; QZ = null;
  if (toStudy) { VIEW = back || VIEW; O.openDash("study"); }
}
function frameFor(q) {
  const r = O.byId.get(q.place); if (!r) return null;
  const fk = q.frame || parentKey(q.place);
  const fr = fk && (O.byId.get(fk) || (O.tnode(fk) && { 6: O.tnode(fk)[2] }));
  let b = fr && fr[6];
  // a frame much larger than the place would make it a speck: widen the place instead
  const span = (x) => (x[2] - x[0]) * (x[3] - x[1]);
  if (!b || span(b) > span(r[6]) * 400 || span(b) === 0) { const w = Math.max(r[6][2] - r[6][0], 0.02) * 1.6, h = Math.max(r[6][3] - r[6][1], 0.015) * 1.6;
    b = [r[6][0] - w, r[6][1] - h, r[6][2] + w, r[6][3] + h]; }
  return b;
}
function show() {
  const q = QZ.qs[QZ.i], el = card();
  QZ.answered = false;
  pinClear();
  O.quizMode(q.kind === "find" || q.kind === "pin" ? "find" : true);
  O.clearSelected();
  const head = '<div class="qz-h"><span class="qz-t">' + esc(QZ.title) + '</span><span class="qz-n">' + (QZ.i + 1) + " / " + QZ.qs.length + '</span><button class="qz-x" data-qz="close" aria-label="' + t_("Close the quiz") + '">✕</button></div>' +
    '<div class="qz-bar"><i style="width:' + (100 * QZ.i / QZ.qs.length).toFixed(1) + '%"></i></div>';
  let body = '<p class="qz-q">' + esc(q.q) + "</p>" + (q.sub ? '<p class="qz-sub">' + esc(q.sub) + "</p>" : "");
  if (q.kind === "mc") body += optsHtml(q);
  else if (q.kind === "clues") body += cluesHtml(q) + optsHtml(q);
  else if (q.kind === "order") { q.pick = []; q.shown = q.shown || shuffle(q.items.map((x, i) => i)); body += '<p class="qz-hint">' + t_("Tap them in order.") + "</p>" + orderHtml(q); }
  else if (q.kind === "pairs") { q.done = new Set(); q.miss = 0; q.sel = null; q.right = q.right || shuffle(q.pairs.map((x, i) => i)); body += '<p class="qz-hint">' + t_("Tap one on the left, then its partner on the right.") + "</p>" + pairsHtml(q); }
  else if (q.kind === "pin") body += '<p class="qz-hint">' + t_("Tap the map where you think it is.") + "</p>";
  else body += '<p class="qz-hint">' + t_("Tap the place on the map.") + '</p><div class="qz-o"><button data-qz="giveup" class="ghost">' + t_("Show me") + "</button></div>";
  el.innerHTML = head + body + '<div class="qz-f" id="qz-f" hidden></div>';
  // the map: an outlined place for "identify", the area around for "find" and "pin", the place itself for other questions about a place
  if (q.kind === "pin") O.fitTo(q.box, "region");
  else if (q.map) {
    const b = frameFor(q); if (b) O.fitTo(b, "appellation");
    if (q.map === "identify") setTimeout(() => O.markSelected(q.place), 50);
  }
}
const optsHtml = (q) => '<div class="qz-o">' + q.options.map((o, i) => '<button data-opt="' + i + '">' + esc(o) + "</button>").join("") + "</div>";
function cluesHtml(q) {
  const left = q.clues.length + 1 - q.shown;
  return '<ol class="qz-clues">' + q.clues.slice(0, q.shown).map((c) => "<li>" + esc(c) + "</li>").join("") + (q.shown > q.clues.length ? "<li>" + t_("Its outline is on the map.") + "</li>" : "") + "</ol>" +
    '<div class="qz-row qz-cluebar"><span class="qz-pts">' + t_("{n} points if right", { n: cluePts(q) }) + "</span>" +
    (left > 0 ? '<button class="ghost" data-qz="clue">' + t_("Another clue") + " (" + left + ")</button>" : "") + "</div>";
}
const cluePts = (q) => Math.max(20, 120 - 20 * q.shown);
function orderHtml(q) {
  return '<ol class="qz-pick">' + q.pick.map((i) => '<li><button data-qz-unpick="' + i + '">' + esc(q.items[i]) + "</button></li>").join("") + "</ol>" +
    '<div class="qz-o qz-pool">' + q.shown.filter((i) => !q.pick.includes(i)).map((i) => '<button data-qz-pick="' + i + '">' + esc(q.items[i]) + "</button>").join("") + "</div>" +
    (q.pick.length === q.items.length ? '<div class="qz-row"><button class="primary" data-qz="check">' + t_("Check") + "</button></div>" : "");
}
function pairsHtml(q) {
  const L = q.pairs.map((p, i) => '<button data-qz-l="' + i + '"' + (q.done.has(i) ? ' class="right" disabled' : q.sel === i ? ' class="sel"' : "") + ">" + esc(p[0]) + "</button>").join("");
  const R = q.right.map((i) => '<button data-qz-r="' + i + '"' + (q.done.has(i) ? ' class="right" disabled' : "") + ">" + esc(q.pairs[i][1]) + "</button>").join("");
  return '<div class="qz-pairs"><div>' + L + "</div><div>" + R + "</div></div>";
}
function redraw(sel, html) { const el = card().querySelector(sel); if (el) el.outerHTML = html; }
function answer(ok, chosen, extra = {}) {
  if (QZ.answered) return;
  QZ.answered = true;
  const q = QZ.qs[QZ.i], el = card();
  countAnswer(q.key, ok);
  const pts = extra.pts != null ? extra.pts : q.kind === "clues" ? (ok ? cluePts(q) : 0) : ok ? 100 : 0;
  const grade = extra.grade != null ? extra.grade : ok ? (q.kind === "clues" && q.shown > 2 ? 1 : 2) : 0;
  QZ.pts += pts; QZ.grades.push(grade);
  if (ok) QZ.right++; else if (q.key) QZ.missed.push(q.key);
  el.querySelectorAll("[data-opt]").forEach((b) => {
    const i = +b.dataset.opt; b.disabled = true;
    if (i === q.answer) b.classList.add("right"); else if (i === chosen) b.classList.add("wrong");
  });
  el.querySelectorAll('[data-qz="giveup"], [data-qz="clue"], [data-qz="check"], [data-qz-pick], [data-qz-unpick]').forEach((b) => { b.disabled = true; });
  if (q.kind === "clues" && q.shown <= q.clues.length) { const ol = el.querySelector(".qz-clues"); if (ol) ol.innerHTML += q.clues.slice(q.shown).map((c) => '<li class="late">' + esc(c) + "</li>").join(""); }
  O.quizMode(true);
  if (q.place) { O.markSelected(q.place); const r = O.byId.get(q.place); if (r && q.map !== "identify" && isArea(r)) O.fitTo(q.kind === "pin" ? [Math.min(q.box[0], r[6][0]), Math.min(q.box[1], r[6][1]), Math.max(q.box[2], r[6][2]), Math.max(q.box[3], r[6][3])] : frameFor(q) || r[6], q.kind === "pin" ? "region" : r[3]); }
  const name = q.place ? (O.byId.get(q.place) || [""])[0] : "";
  const f = $("qz-f");
  f.hidden = false;
  f.className = "qz-f " + (ok ? "ok" : "no");
  const last = QZ.i === QZ.qs.length - 1;
  const head = ok ? (grade === 1 && q.kind === "pin" ? t_("Close enough.") : t_("Right.")) : q.kind === "find" || q.kind === "pin" ? t_("Here it is.") : t_("Not quite.");
  const sol = q.kind === "order" ? '<ol class="qz-sol">' + q.items.map((x, i) => "<li" + (q.pick[i] === i ? ' class="ok"' : "") + ">" + esc(x) + "</li>").join("") + "</ol>" : "";
  f.innerHTML = "<b>" + head + "</b> " + (extra.note ? esc(extra.note) + " " : "") + (pts && q.game ? '<span class="qz-pts">+' + pts + "</span> " : "") + sol + (q.explain ? esc(q.explain) : "") +
    (q.note ? '<p class="qz-note">' + esc(q.note) + "</p>" : "") +
    '<div class="qz-row"><button class="primary" data-qz="next">' + (last ? t_("See your score") : t_("Next")) + " →</button>" +
    (name ? '<button class="ghost" data-qz="open" data-id="' + esc(q.place) + '">' + t_("Open {name}", { name: esc(name) }) + "</button>" : "") + "</div>";
  f.querySelector('[data-qz="next"]').focus();
}
function next() {
  if (QZ.i < QZ.qs.length - 1) {
    if (leftToday() <= 0) return paywall();
    QZ.i++; return show();
  }
  finish();
}
function finish() {
  O.quizMode(true); O.clearSelected(); pinClear();
  const el = card(), n = QZ.qs.length, pct = Math.round(100 * QZ.right / n), m = QZ.meta || {};
  let extra = "";
  if (m.game) {
    const st = ST(); st.best = st.best || {};
    const best = st.best[m.game] || 0, isBest = m.game !== "daily" && QZ.pts > best && n >= 3;
    if (isBest) st.best[m.game] = QZ.pts;
    if (m.game === "daily") {
      st.daily = st.daily || {};
      const marks = QZ.grades.map((g) => (g === 2 ? "🟩" : g === 1 ? "🟨" : "🟥")).join("");
      st.daily[m.day] = { m: marks, r: QZ.right, n, p: QZ.pts, c: m.country };
      const keys = Object.keys(st.daily).sort(); if (keys.length > 60) keys.slice(0, keys.length - 60).forEach((k) => delete st.daily[k]);
      extra = '<p class="qz-marks">' + marks + "</p>";
    }
    save();
    extra += '<p class="qz-ptsline">' + t_("{n} points", { n: O.fmtN(QZ.pts) }) + (isBest ? " · " + t_("New personal best!") : best && m.game !== "daily" ? " · " + t_("Best: {n}", { n: O.fmtN(best) }) : "") + "</p>";
  }
  el.innerHTML = '<div class="qz-h"><span class="qz-t">' + esc(QZ.title) + '</span><button class="qz-x" data-qz="close" aria-label="' + t_("Close the quiz") + '">✕</button></div>' +
    '<div class="qz-end"><b>' + QZ.right + " / " + n + "</b><span>" + (pct >= 90 ? t_("Excellent.") : pct >= 70 ? t_("Well done.") : pct >= 50 ? t_("Good start. The misses come back in your review.") : t_("Keep going. The misses come back in your review.")) + "</span>" + extra + "</div>" +
    '<div class="qz-row">' + (m.game === "daily" ? '<button class="primary" data-qz="share">' + t_("Share my score") + "</button>" : "") +
    (m.game && m.game !== "daily" ? '<button class="primary" data-qz="again">' + t_("Play again") + "</button>" : "") +
    (QZ.missed.length ? '<button class="' + (m.game ? "ghost" : "primary") + '" data-qz="missed">' + t_("Try the {n} misses again", { n: QZ.missed.length }) + "</button>" : "") +
    '<button class="ghost" data-qz="study">' + t_("Back to Study") + "</button></div>";
}
function paywall() {
  O.quizMode(true); O.clearSelected();
  const el = card();
  el.innerHTML = '<div class="qz-h"><span class="qz-t">' + esc(QZ.title) + '</span><button class="qz-x" data-qz="close" aria-label="' + t_("Close the quiz") + '">✕</button></div>' + paywallHtml();
}
function paywallHtml() {
  return '<div class="qz-pay"><b>' + t_("That was today's {n} free questions.", { n: FREE_PER_DAY }) + "</b><p>" +
    t_("Members study without limits: every lesson, every quiz and the full review. Free questions come back tomorrow.") + " " +
    t_("Membership opens soon: reserve a Founding spot now, nothing to pay until then.") + "</p>" +
    '<a class="primary" href="/founding?from=study">' + t_("Reserve my Founding spot") + " →</a></div>";
}
async function missedAgain() {
  const keys = QZ.missed.slice(), title = QZ.title, back = QZ.back;
  const qs = (await Promise.all(keys.map(fromKey))).filter(Boolean);
  QZ = null; start(title, qs, back);
}
function onMapClick(e) {
  if (!QZ || QZ.answered) return;
  const q = QZ.qs[QZ.i];
  if (q.kind === "pin") return pinAnswer(e);
  if (q.kind !== "find") return;
  const ids = O.placesAt(e.point);
  const ok = ids.includes(q.place) || ids.some((id) => O.pathOf(id).includes(q.place));
  if (!ids.length) return O.toast(t_("Tap inside an outline."));
  answer(ok, -1);
}
// order and pairs: taps build the answer
function gameTap(d) {
  const q = QZ.qs[QZ.i];
  if (q.kind === "order") {
    if (d.qzPick != null && !q.pick.includes(+d.qzPick)) q.pick.push(+d.qzPick);
    else if (d.qzUnpick != null) q.pick = q.pick.filter((x) => x !== +d.qzUnpick);
    const el = card(); el.querySelector(".qz-pick").remove(); const pool = el.querySelector(".qz-pool"); const row = pool.nextElementSibling && pool.nextElementSibling.classList.contains("qz-row") ? pool.nextElementSibling : null; if (row) row.remove();
    pool.outerHTML = orderHtml(q);
    return;
  }
  if (q.kind === "pairs") {
    let wrong = false;
    if (d.qzL != null) q.sel = +d.qzL;
    else if (d.qzR != null && q.sel != null) {
      if (+d.qzR === q.sel) { q.done.add(q.sel); q.sel = null; }
      else { q.miss++; wrong = true; q.sel = null; const b = card().querySelector('[data-qz-r="' + d.qzR + '"]'); if (b) b.classList.add("wrong"); }
    } else return;
    setTimeout(() => {
      if (!QZ || QZ.qs[QZ.i] !== q) return;
      const box = card().querySelector(".qz-pairs"); if (box) box.outerHTML = pairsHtml(q);
      if (q.done.size === q.pairs.length) { const n = q.pairs.length, first = Math.max(0, n - q.miss); answer(q.miss <= 1, -1, { pts: Math.round(100 * first / n), grade: q.miss === 0 ? 2 : 1 + (q.miss <= 1 ? 0 : -1), note: q.miss ? t_("{n} wrong tries.", { n: q.miss }) : t_("No wrong tries.") }); }
    }, wrong ? 450 : 0);
  }
}
document.addEventListener("click", (e) => {
  const o = e.target.closest("#quiz [data-opt]");
  if (o && QZ && !QZ.answered) { const i = +o.dataset.opt; return answer(i === QZ.qs[QZ.i].answer, i); }
  const g = e.target.closest("#quiz [data-qz-pick], #quiz [data-qz-unpick], #quiz [data-qz-l], #quiz [data-qz-r]");
  if (g && QZ && !QZ.answered) return gameTap(g.dataset);
  const b = e.target.closest("#quiz [data-qz]");
  if (!b || !QZ) return;
  const a = b.dataset.qz;
  if (a === "clue") {
    const q = QZ.qs[QZ.i]; if (QZ.answered || q.shown > q.clues.length) return;
    q.shown++;
    if (q.shown > q.clues.length) { q.map = "identify"; const fb = frameFor(q); if (fb) O.fitTo(fb, "appellation"); setTimeout(() => O.markSelected(q.place), 50); }
    redraw(".qz-clues", ""); redraw(".qz-cluebar", cluesHtml(q));
    return;
  }
  if (a === "check") { const q = QZ.qs[QZ.i]; const right = q.pick.filter((x, i) => x === i).length; return answer(right === q.items.length, -1, { pts: Math.round(100 * right / q.items.length), grade: right === q.items.length ? 2 : right >= q.items.length - 2 ? 1 : 0 }); }
  if (a === "share") { if (QZ.meta && QZ.meta.day) dailyShare(QZ.meta.day); return; }
  if (a === "again") { const m = QZ.meta; stop(false); return play(m.game, m.theme); }
  if (a === "close") stop(true);
  else if (a === "next") next();
  else if (a === "giveup") answer(false, -1);
  else if (a === "missed") missedAgain();
  else if (a === "study") stop(true);
  else if (a === "open") { const r = O.byId.get(b.dataset.id); stop(false); if (r) O.goTo(r); }
});
document.addEventListener("keydown", (e) => {
  if (!QZ || $("quiz")?.hidden) return;
  if (e.key === "Escape") { stop(true); return; }
  if (e.target.closest("input, textarea")) return;
  const q = QZ.qs[QZ.i];
  if (!QZ.answered && q && (q.kind === "mc" || q.kind === "clues") && /^[1-4]$/.test(e.key) && +e.key <= q.options.length) { e.preventDefault(); answer(+e.key - 1 === q.answer, +e.key - 1); }
  else if (QZ.answered && e.key === "Enter") { e.preventDefault(); next(); }
});

// ---------- launching
async function begin(title, make, back) {
  if (leftToday() <= 0) { VIEW = Object.assign({}, VIEW, { pay: true }); O.renderDash(); return; }
  O.toast(t_("Preparing your questions…"));
  try { const qs = await make(); start(title, qs.slice(0, member() ? qs.length : Math.min(qs.length, Math.max(leftToday(), 1))), back); }
  catch (e) { console.warn("study", e); O.toast(t_("The questions could not be loaded right now.")); }
}
async function drillQs(path, kinds, n = SESSION) {
  const recs = placesIn(path.scope);
  await detailsFor(recs);
  return buildDrill(recs, kinds, n, focusOf(path));
}
async function reviewQs() {
  const keys = dueKeys().slice(0, 20);
  return (await Promise.all(keys.map((k) => fromKey(k).catch(() => null)))).filter(Boolean);
}

// ---------- games: seven ways to play, each over a theme (a path, a level, a region, a grape or everything)
// Data games are built from the atlas (outlines, terrain, rock, grapes, the LWIN wines); the curated sets (odd one
// out, pairs, order) come from the lessons. Everything counts in the same free answers a day.
const GAMES = [
  { id: "daily", icon: "☀", name: N_("Daily challenge"), desc: N_("Five questions, the same for everyone today. Share your score."), n: 5 },
  { id: "mystery", icon: "?", name: N_("Mystery place"), desc: N_("Clue by clue: the slope, the rock, the grapes, the nearest town. Guess early for more points."), n: 5 },
  { id: "pin", icon: "⌖", name: N_("Pin it"), desc: N_("Drop a pin on the map. The closer, the more points."), n: 8 },
  { id: "order", icon: "↕", name: N_("In order"), desc: N_("North to south, lowest to highest, first to last: put them in line."), n: 5 },
  { id: "where", icon: "◉", name: N_("Where is it from?"), desc: N_("A real wine and its producer. Which appellation is it from?"), n: 8 },
  { id: "odd", icon: "≠", name: N_("Odd one out"), desc: N_("Four answers, one does not belong. Which one, and why?"), n: 8 },
  { id: "match", icon: "⇄", name: N_("Match"), desc: N_("Pair them up: places and grapes, villages and regions, terms and meanings."), n: 4 },
];
const GAME = new Map(GAMES.map((g) => [g.id, g]));
// the countries a round over "everything" or the daily challenge draws its map questions from
const ROUND_CC = ["g:FR", "g:IT", "g:ES", "g:PT", "g:DE", "g:AT", "g:US", "g:AU", "g:NZ", "g:ZA", "g:CL", "g:AR", "g:GR", "g:HU"];
// grapes for the grape theme, with the names the registers use for them; where the registers name the grapes
const GRAPES = {
  "Cabernet Sauvignon": [[], ["g:FR", "g:IT", "g:ES"]], "Merlot": [[], ["g:FR", "g:IT"]], "Cabernet Franc": [["Breton"], ["g:FR"]],
  "Pinot Noir": [["Spätburgunder", "Pinot Nero", "Blauburgunder"], ["g:FR", "g:DE", "g:IT"]], "Chardonnay": [[], ["g:FR", "g:IT"]],
  "Syrah": [["Shiraz"], ["g:FR"]], "Grenache": [["Garnacha", "Garnacha Tinta", "Cannonau", "Garnatxa", "Grenache Noir"], ["g:FR", "g:ES", "g:IT"]],
  "Mourvèdre": [["Monastrell", "Mataro"], ["g:FR", "g:ES"]], "Carignan": [["Cariñena", "Mazuelo", "Samsó", "Carignano"], ["g:FR", "g:ES"]],
  "Tempranillo": [["Tinta Roriz", "Aragonez", "Tinto Fino", "Tinta del País", "Tinta de Toro", "Cencibel", "Ull de Llebre"], ["g:ES", "g:PT"]],
  "Nebbiolo": [["Spanna", "Chiavennasca"], ["g:IT"]], "Sangiovese": [["Prugnolo Gentile", "Sangiovese Grosso", "Morellino"], ["g:IT"]],
  "Barbera": [[], ["g:IT"]], "Corvina": [["Corvina Veronese"], ["g:IT"]], "Aglianico": [[], ["g:IT"]], "Nero d'Avola": [["Calabrese"], ["g:IT"]],
  "Malbec": [["Côt", "Cot"], ["g:FR"]], "Gamay": [[], ["g:FR"]], "Zinfandel": [["Primitivo"], ["g:IT"]], "Touriga Nacional": [[], ["g:PT"]],
  "Blaufränkisch": [["Lemberger", "Kékfrankos", "Frankovka"], ["g:AT", "g:HU"]], "Pinotage": [[], []], "Carmenère": [[], []], "Tannat": [[], ["g:FR"]],
  "Saperavi": [[], []], "Xinomavro": [[], ["g:GR"]], "Agiorgitiko": [[], ["g:GR"]],
  "Riesling": [["Riesling Renano", "Weisser Riesling", "Rheinriesling"], ["g:DE", "g:FR", "g:AT"]], "Sauvignon Blanc": [["Sauvignon"], ["g:FR", "g:AT"]],
  "Chenin Blanc": [["Chenin", "Steen"], ["g:FR"]], "Sémillon": [["Semillon"], ["g:FR"]], "Viognier": [[], ["g:FR"]],
  "Gewurztraminer": [["Gewürztraminer", "Traminer Aromatico", "Savagnin Rose"], ["g:FR", "g:DE", "g:IT"]],
  "Pinot Gris": [["Pinot Grigio", "Grauburgunder", "Ruländer"], ["g:FR", "g:IT", "g:DE"]], "Pinot Blanc": [["Pinot Bianco", "Weissburgunder"], ["g:FR", "g:DE", "g:IT"]],
  "Grüner Veltliner": [["Veltliner", "Grüner Veltliner"], ["g:AT"]], "Muscat": [["Moscato", "Moscatel", "Muskateller", "Muscat à petits grains", "Muscat Blanc à Petits Grains", "Moscato Bianco"], ["g:FR", "g:IT", "g:GR", "g:ES"]],
  "Albariño": [["Alvarinho"], ["g:ES", "g:PT"]], "Verdejo": [[], ["g:ES"]], "Godello": [[], ["g:ES"]], "Palomino": [["Palomino Fino", "Listán"], ["g:ES"]],
  "Furmint": [[], ["g:HU"]], "Assyrtiko": [[], ["g:GR"]], "Glera": [[], ["g:IT"]], "Garganega": [[], ["g:IT"]],
  "Melon de Bourgogne": [["Melon"], ["g:FR"]], "Vermentino": [["Rolle"], ["g:IT", "g:FR"]],
};
// a register's grape name ("Pinot Noir N", "Spätburgunder") is this grape?
const grapeIs = (g, names) => { const syn = GRAPES[g] ? [g, ...GRAPES[g][0]] : [g]; const s = new Set(syn.map(plain)); return (names || []).some((n) => s.has(plain(n))); };
// a curated text mentions this grape? (short synonyms such as "Sauvignon" or "Melon" would mislead in free text)
function textHasGrape(g, text) {
  if (!g) return true;
  const t = " " + plain(text) + " ";
  return [g, ...(GRAPES[g] ? GRAPES[g][0] : [])].filter((s) => !["Sauvignon", "Melon", "Breton", "Cot", "Listán", "Chenin", "Calabrese"].includes(s))
    .some((s) => t.includes(" " + plain(s) + " "));
}
const THEME_KEY = "studyTheme";
const getTheme = () => store.get(THEME_KEY) || "all";

// ---------- randomness: Math.random, or a seeded one for the daily challenge (the same for everyone)
function seeded(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) { h = Math.imul(h ^ str.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
  let a = h >>> 0;
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
function withRandom(rnd, fn) { const M = Math.random; Math.random = rnd; try { return fn(); } finally { Math.random = M; } }

// ---------- the wines of "Where is it from?" (pipeline/game_wines.py, LWIN by Liv-ex, CC BY 4.0)
let GW = null, gwLoading = null;
function loadGameWines() {
  if (!gwLoading) gwLoading = fetch("/data/game-wines.json").then((r) => r.json()).then((j) => { GW = j.w || []; return GW; }).catch((e) => { gwLoading = null; GW = []; return GW; });
  return gwLoading;
}
const WINE_KIND = { r: N_("red"), w: N_("white"), p: N_("rosé"), s: N_("sparkling"), f: N_("fortified"), d: N_("sweet") };

// ---------- the theme of a round: which paths (curated sets) and which atlas places (data games)
async function themeCtx(theme, rnd = Math.random) {
  await loadData();
  const [type, ...rest] = String(theme || "all").split(":"), val = rest.join(":");
  const ctx = { theme, type, label: t_("Everything"), paths: DATA.paths, keys: [], grape: null, recs: [], pool: [], focus: new Set() };
  if (type === "path" && DATA.byPath.has(val)) { const p = DATA.byPath.get(val); ctx.paths = [p]; ctx.keys = (p.scope || []).slice(); ctx.label = p.title; }
  else if (type === "level") { ctx.paths = DATA.paths.filter((p) => p.level === val); ctx.label = t_(val); }
  else if (type === "region" && O.tnode(val)) {
    ctx.keys = [val]; ctx.label = nameOf(val);
    ctx.paths = DATA.paths.filter((p) => (p.scope || []).some((s) => s === val || s.startsWith(val + "/") || val.startsWith(s + "/")));
  } else if (type === "grape" && GRAPES[val]) { ctx.grape = val; ctx.label = val; }
  else if (type === "daily") { ctx.keys = [val]; ctx.label = nameOf(val); ctx.paths = DATA.paths.filter((p) => (p.scope || []).some((s) => s === val || s.startsWith(val + "/"))); }
  ctx.paths.forEach((p) => focusOf(p).forEach((id) => ctx.focus.add(id)));
  // a theme with no map of its own (a thematic path, a level, a grape, everything) plays its map games in one country
  if (!ctx.keys.length) {
    if (type === "path" && ctx.focus.size) ctx.recs = [...ctx.focus].map((id) => O.byId.get(id)).filter(Boolean);
    else {
      const scoped = ctx.paths.filter((p) => p.scope && p.scope.length);
      let cc;
      if (ctx.grape) { const l = GRAPES[ctx.grape][1]; cc = l.length ? l[Math.floor(rnd() * l.length)] : null; }
      else if (type === "level" && scoped.length) { const p = scoped[Math.floor(rnd() * scoped.length)]; ctx.keys = p.scope.slice(); ctx.label += " · " + p.title; }
      else cc = ROUND_CC[Math.floor(rnd() * ROUND_CC.length)];
      if (cc) { ctx.keys = [cc]; ctx.label += " · " + nameOf(cc); }
    }
  }
  if (ctx.keys.length) ctx.recs = placesIn(ctx.keys);
  ctx.pool = ctx.recs;
  await detailsFor(ctx.recs);
  if (ctx.grape) ctx.recs = ctx.recs.filter((r) => grapeIs(ctx.grape, mainGrapes(det(r[1]))));
  ctx.ids = new Set(ctx.recs.map((r) => r[1]));
  return ctx;
}
// the lessons' curated sets of one kind ("odd", "pairs", "order") or their questions ("questions"), for a theme
function curated(ctx, kind) {
  const out = [];
  ctx.paths.forEach((p) => p.lessons.forEach((l) => (l[kind] || []).forEach((x, i) => {
    if (ctx.grape && !(kind === "questions" ? grapeIsList(ctx.grape, x.grapes) || textHasGrape(ctx.grape, x.q + " " + x.options[x.answer]) : textHasGrape(ctx.grape, JSON.stringify(x)))) return;
    if (ctx.type === "region" && kind === "questions" && x.place && !ctx.ids.has(x.place)) return;
    out.push({ l, x, i });
  })));
  return out;
}
const grapeIsList = (g, list) => (list || []).some((x) => grapeIs(g, [x]) || plain(x) === plain(g));

// ---------- picking places: famous ones more often, the places the lessons talk about most
function pickTarget(ctx, ok) {
  const list = ctx.recs.filter(ok);
  if (!list.length) return null;
  let tot = 0; const cum = list.map((r) => (tot += weightOf(r) * (ctx.focus.has(r[1]) ? 6 : 1)));
  const x = Math.random() * tot; let lo = 0, hi = cum.length - 1;
  while (lo < hi) { const m = (lo + hi) >> 1; if (cum[m] < x) lo = m + 1; else hi = m; }
  return list[lo];
}
// a region of the map, not a category such as "Regional appellations" that spreads over its neighbours
function isGeo(k) {
  if (!k || /^g:[A-Z]{2}$/.test(k)) return false;
  const n = O.tnode(k);
  if (!n || !n[2]) return true;
  const par = O.pathOf(k), up = par.length > 1 ? par[par.length - 2] : null;
  const sibs = up ? (O.kidsOf(up) || []).filter((x) => x !== k && O.tnode(x) && O.tnode(x)[2]) : [];
  return sibs.every((x) => overlap(n[2], O.tnode(x)[2]) < 0.5);
}
// grands crus that cross village lines sit under one village in the atlas tree; AVAs can span states: no "lies in"
const oneHome = (r) => !(r[2] === "FR" && r[4] === "grand_cru") && (det(r[1]).states || []).length <= 1;
const related = (a, b) => a === b || O.pathOf(a).includes(b) || O.pathOf(b).includes(a);
// four names for "which place is it?": siblings first, never an outline that covers the same ground
function placeOptions(r, pool) {
  const par = parentKey(r[1]);
  const apart = (x) => x && x[1] !== r[1] && isArea(x) && overlap(x[6], r[6]) < 0.5 && !related(x[1], r[1]) && nm(x) !== nm(r);
  let sib = par ? (O.kidsOf(par) || []).map((k) => O.byId.get(k)).filter(apart) : [];
  if (sib.length < 3) sib = sib.concat(pool.filter((x) => apart(x) && x[3] === r[3] && !sib.includes(x)));
  return sib;
}
const km = (a, b) => { const R = 6371, d = Math.PI / 180, x = Math.sin((b[1] - a[1]) * d / 2) ** 2 + Math.cos(a[1] * d) * Math.cos(b[1] * d) * Math.sin((b[0] - a[0]) * d / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(x)); };
const centre = (r) => { const d = det(r[1]); return d.lon != null ? [d.lon, d.lat] : [(r[6][0] + r[6][2]) / 2, (r[6][1] + r[6][3]) / 2]; };
const areaHa = (r) => { const d = det(r[1]); return d.area_ha || d.outline_area_ha || d.vine_area_ha || null; };
const sig2 = (v) => { const p = Math.pow(10, Math.max(0, Math.floor(Math.log10(v)) - 1)); return Math.round(v / p) * p; };

// ---------- the clues of a mystery place, hardest first
function clueList(r) {
  const d = det(r[1]), c = [], name = r[0];
  const add = (text, ...giveaways) => { if (text && !giveaways.some((g) => g && (givesAway(name, g) || givesAway(g, name)))) c.push(text); };
  if (d.terrain && O.terrainText) add(O.terrainText(d.terrain));
  const b = (d.bedrock || [])[0]; if (b && b[1] >= 40) add(t_("The rock below is mostly {rock}.", { rock: t_(b[0]) }));
  const ha = areaHa(r); if (ha && ha > 1) add(t_("It covers about {ha} ha.", { ha: O.fmtN(sig2(ha)) }));
  if (d.sea_km != null) add(d.sea_km < 5 ? t_("The sea is right there.") : t_("The sea is {km} km away.", { km: O.fmtN(sig2(d.sea_km)) }));
  const rv = (d.rivers || [])[0]; if (rv) add(t_("A river nearby: the {river}.", { river: rv[0] }), rv[0]);
  const g = mainGrapes(d); if (g.length && g.length <= 3) add(t_("Main grapes: {list}.", { list: g.join(", ") }), ...g);
  const par = parentKey(r[1]); if (par && isGeo(par) && oneHome(r)) add(t_("It lies in {parent}.", { parent: nameOf(par) }), nameOf(par));
  const tw = d.near_town; if (tw) add(t_("The nearest town: {town}, {km} km away.", { town: tw[0], km: O.fmtN(Math.max(1, Math.round(tw[1]))) }), tw[0]);
  return c;
}

// ---------- builders: (ctx) -> a question, or null to try again. uid: no repeats in a round; key: a review card
const BUILD = {
  mystery(ctx) {
    const r = pickTarget(ctx, (x) => isArea(x) && x[3] !== "vineyard");
    if (!r) return null;
    const clues = clueList(r);
    if (clues.length < 3) return null;
    const q = mc("g:mystery:" + r[1], t_("Which place is it?"), nm(r), placeOptions(r, ctx.pool).map(nm), { place: r[1] });
    if (!q) return null;
    return Object.assign(q, { kind: "clues", uid: "m" + r[1], clues: clues.slice(0, 5), shown: 1, map: null, mapClue: true, note: det(r[1]).atlas_note || "", explain: lies(r) });
  },
  pin(ctx) {
    const r = pickTarget(ctx, (x) => isArea(x));
    if (!r) return null;
    const span = (b) => Math.max(1e-9, (b[2] - b[0]) * (b[3] - b[1]));
    // the frame: the nearest region around it that is clearly larger, so the pin is a real choice
    let frame = null;
    for (const k of O.pathOf(r[1]).slice(0, -1).reverse()) {
      const b = (O.byId.get(k) || [])[6] || (O.tnode(k) || [])[2];
      if (b && span(b) >= span(r[6]) * 40) { frame = b; break; }
    }
    if (!frame) { const c = O.tnode("g:" + r[2]); frame = c && c[2]; }
    if (!frame) return null;
    const diag = km([frame[0], frame[1]], [frame[2], frame[3]]);
    return { key: "g:pin:" + r[1], uid: "p" + r[1], kind: "pin", q: t_("Drop a pin on {name}.", { name: nm(r) }), place: r[1], box: frame, diag, explain: lies(r) };
  },
  order(ctx) { return Math.random() < 0.5 ? curatedOrder(ctx) || dataOrder(ctx) : dataOrder(ctx) || curatedOrder(ctx); },
  where(ctx) {
    if (!GW || !GW.length) return null;
    let list = GW.filter((w) => ctx.ids.has(w[2]));
    if (ctx.grape) list = list.filter((w) => textHasGrape(ctx.grape, w[1]) || grapeIs(ctx.grape, mainGrapes(det(w[2]))));
    if (!list.length) return null;
    const w = pick1(list), r = O.byId.get(w[2]);
    if (!r) return null;
    const near = placeOptions(r, ctx.pool), gwPlaces = new Set(GW.map((x) => x[2]));
    // prefer places that have famous wines of their own, then any of the same kind
    const wrong = shuffle(near.filter((x) => gwPlaces.has(x[1]))).concat(shuffle(near));
    const q = mc("w:" + w[4], t_("Where is this wine from?"), nm(r), wrong.map(nm), { place: r[1] });
    if (!q) return null;
    return Object.assign(q, { uid: "w" + w[4], sub: w[0] + " · " + w[1] + (WINE_KIND[w[3]] ? " · " + t_(WINE_KIND[w[3]]) : ""),
      explain: t_("{wine} by {producer} comes from {place}.", { wine: w[1], producer: w[0], place: r[0] }) + " " + lies(r) });
  },
  odd(ctx) { return Math.random() < 0.5 ? curatedOdd(ctx) || dataOdd(ctx) : dataOdd(ctx) || curatedOdd(ctx); },
  match(ctx) { return Math.random() < 0.5 ? curatedPairs(ctx) || dataPairs(ctx) : dataPairs(ctx) || curatedPairs(ctx); },
};
function curatedOdd(ctx) {
  const c = curated(ctx, "odd"); if (!c.length) return null;
  const { l, x, i } = pick1(c), order = shuffle([0, 1, 2, 3]);
  return { key: "o:" + l.id + ":" + i, uid: "o" + l.id + i, kind: "mc", q: x.q || t_("Which one does not belong?"), options: order.map((k) => x.items[k]), answer: order.indexOf(x.odd), explain: x.why, from: l.title };
}
function dataOdd(ctx) {
  const kinds = shuffle(["region", "rank", "grape"]);
  for (const k of kinds) {
    if (k === "region") {
      const r = pickTarget(ctx, (x) => isArea(x)); if (!r) continue;
      const P = parentKey(r[1]); if (!P || !isGeo(P)) continue;
      const G = parentKey(P); if (!G) continue;
      const kidsIn = (k2) => (O.kidsOf(k2) || []).map((id) => O.byId.get(id)).filter((x) => x && isArea(x) && oneHome(x) && !givesAway(x[0], nameOf(P)));
      const same = shuffle(kidsIn(P)).slice(0, 3);
      const others = (O.kidsOf(G) || []).filter((k2) => k2 !== P && (O.kidsOf(k2) || []).length);
      if (same.length < 3 || !others.length) continue;
      const Q = pick1(others), Pbox = (O.tnode(P) || [])[2];
      if (!isGeo(Q)) continue;
      const odd = pick1(kidsIn(Q).filter((x) => !givesAway(x[0], nameOf(Q)) && !same.some((s) => nm(s) === nm(x)) && (!Pbox || overlap(x[6], Pbox) < 0.2)));
      if (!odd) continue;
      const items = shuffle([...same, odd]);
      return { key: null, uid: "or" + odd[1], kind: "mc", q: t_("Which one is not in {region}?", { region: nameOf(P) }), options: items.map(nm), answer: items.indexOf(odd), place: odd[1],
        explain: t_("{name} lies in {parent}.", { name: nm(odd), parent: nameOf(Q) }) };
    }
    if (k === "rank") {
      const top = ctx.pool.filter((x) => (x[2] === "IT" && x[4] === "docg") || (x[2] === "FR" && x[4] === "grand_cru"));
      if (top.length < 3) continue;
      const cc = pick1(top)[2], same = shuffle(top.filter((x) => x[2] === cc)).slice(0, 3);
      const lower = ctx.pool.filter((x) => x[2] === cc && (cc === "IT" ? x[3] === "appellation" && x[4] !== "docg" : x[4] === "premier_cru" && /^[A-Z]/.test(x[0]) && !/premier cru/i.test(x[0])) && !same.some((s) => s[0] === x[0]));
      if (same.length < 3 || !lower.length) continue;
      const odd = pick1(lower), items = shuffle([...same, odd]);
      const rank = cc === "IT" ? "DOCG" : t_("grand cru");
      return { key: null, uid: "ok" + odd[1], kind: "mc", q: t_("Which one is not a {rank}?", { rank }), options: items.map(nm), answer: items.indexOf(odd), place: odd[1],
        explain: t_("{name} is a {rank}.", { name: nm(odd), rank: cc === "IT" ? "DOC" : t_("premier cru") }) + " " + same.map(nm).join(", ") + ": " + rank + "." };
    }
    if (k === "grape") {
      const single = ctx.pool.filter((x) => mainGrapes(det(x[1])).length === 1);
      const g = ctx.grape || (single.length ? mainGrapes(det(pick1(single)[1]))[0] : null);
      if (!g) continue;
      const withG = shuffle(single.filter((x) => grapeIs(g, mainGrapes(det(x[1]))))).slice(0, 3);
      const without = single.filter((x) => !grapeIs(g, mainGrapes(det(x[1]))) && !givesAway(x[0], g));
      if (withG.length < 3 || !without.length) continue;
      const odd = pick1(without), items = shuffle([...withG, odd]);
      return { key: null, uid: "og" + odd[1], kind: "mc", q: t_("Which one is not made mainly from {grape}?", { grape: g }), options: items.map(nm), answer: items.indexOf(odd), place: odd[1],
        explain: t_("The rules of {name} are built on {grape}.", { name: nm(odd), grape: mainGrapes(det(odd[1]))[0] }) };
    }
  }
  return null;
}
function curatedPairs(ctx) {
  const c = curated(ctx, "pairs"); if (!c.length) return null;
  const { l, x, i } = pick1(c);
  return { key: "x:" + l.id + ":" + i, uid: "x" + l.id + i, kind: "pairs", q: x.title, pairs: x.pairs.slice(), from: l.title };
}
function dataPairs(ctx) {
  for (const k of shuffle(["grape", "region"])) {
    const seen = new Set(), names = new Set(), pairs = [];
    const cands = shuffle(ctx.pool.filter((x) => isArea(x) && x[3] !== "vineyard"));
    for (const r of cands) {
      if (pairs.length >= 5) break;
      let right = null;
      if (k === "grape") { const g = mainGrapes(det(r[1])); if (g.length === 1 && !givesAway(r[0], g[0])) right = g[0]; }
      else { const P = parentKey(r[1]); if (P && isGeo(P) && oneHome(r) && !givesAway(r[0], nameOf(P))) right = nameOf(P); }
      if (ctx.grape && k === "grape" && pairs.length === 0 && !grapeIs(ctx.grape, mainGrapes(det(r[1])))) continue;
      if (!right || seen.has(right) || names.has(nm(r))) continue;
      seen.add(right); names.add(nm(r)); pairs.push([nm(r), right]);
    }
    if (pairs.length >= 4) return { key: null, uid: "x" + pairs.map((p) => p[0]).join("|"), kind: "pairs", q: k === "grape" ? t_("Match each place to its main grape") : t_("Match each place to its region"), pairs };
  }
  return null;
}
function curatedOrder(ctx) {
  const c = curated(ctx, "order"); if (!c.length) return null;
  const { l, x, i } = pick1(c);
  return { key: "r:" + l.id + ":" + i, uid: "r" + l.id + i, kind: "order", q: x.title, items: x.items.slice(), explain: x.why, from: l.title };
}
function dataOrder(ctx) {
  const lat = (x) => centre(x)[1], lon = (x) => centre(x)[0], hi = (x) => { const t = det(x[1]).terrain; return t && t.e ? t.e[1] : null; };
  const CRIT = [
    { title: t_("From north to south"), val: (x) => -lat(x), gap: 0.04, show: () => "" },
    { title: t_("From west to east"), val: lon, gap: 0.06, show: () => "" },
    { title: t_("From lowest to highest, on average"), val: hi, gap: 35, show: (x) => O.fmtN(hi(x)) + " m" },
    // sizes only where the figure is the place's own delimited area (French parcels, AVAs, EU appellation outlines)
    { title: t_("From largest to smallest"), val: (x) => { const d = det(x[1]), a = d.area_ha || (d.basis ? null : d.outline_area_ha); return a ? -Math.log(a) : null; }, gap: 0.3, show: (x) => O.fmtN(sig2(areaHa(x))) + " ha" },
  ];
  const r = pickTarget(ctx, (x) => isArea(x)); if (!r) return null;
  const P = parentKey(r[1]);
  let group = P && isGeo(P) ? (O.kidsOf(P) || []).map((k) => O.byId.get(k)).filter((x) => x && isArea(x)) : [];
  if (group.length < 4) group = ctx.pool.filter((x) => isArea(x) && x[3] === r[3] && isGeo(parentKey(x[1]) || "") === isGeo(parentKey(r[1]) || ""));
  for (const c of shuffle(CRIT.slice())) {
    const pick = [];
    for (const x of shuffle(group.filter((x) => c.val(x) != null))) {
      if (pick.length >= 5) break;
      if (pick.some((y) => Math.abs(c.val(y) - c.val(x)) < c.gap || nm(y) === nm(x))) continue;
      pick.push(x);
    }
    if (pick.length < 4) continue;
    const n = pick.length === 5 && Math.random() < 0.5 ? 4 : pick.length, items = pick.slice(0, n).sort((a, b) => c.val(a) - c.val(b));
    return { key: null, uid: "d" + items.map((x) => x[1]).join("|") + c.title, kind: "order", q: c.title, items: items.map(nm),
      explain: items.map((x) => nm(x) + (c.show(x) ? " " + c.show(x) : "")).join(" · ") };
  }
  return null;
}
function buildGame(gid, ctx, n) {
  const out = [], uids = new Set();
  for (let g = 0; out.length < n && g < n * 40; g++) {
    const q = BUILD[gid](ctx);
    if (q && !uids.has(q.uid)) { uids.add(q.uid); q.game = gid; out.push(q); }
  }
  return out;
}
// the daily challenge: one country a day, five games, the same questions for everyone
const DAILY_MIX = ["mystery", "pin", "where", "odd", "order", "match"];
function dailyCC(day) { return ROUND_CC[Math.floor(seeded("cc" + day)() * ROUND_CC.length)]; }
async function dailyQs(day) {
  const cc = dailyCC(day), ctx = await themeCtx("daily:" + cc);
  await loadGameWines();
  const rnd = seeded("q" + day);
  return { ctx, qs: withRandom(rnd, () => {
    const out = [], uids = new Set();
    for (const gid of DAILY_MIX) {
      if (out.length >= 5) break;
      for (let t = 0; t < 30; t++) { const q = BUILD[gid](ctx); if (q && !uids.has(q.uid)) { uids.add(q.uid); q.game = gid; out.push(q); break; } }
    }
    return out;
  }) };
}
const dailyDone = (day) => (ST().daily || {})[day];
function dailyShare(day) {
  const d = dailyDone(day); if (!d) return;
  const text = "Open Wine Atlas · " + t_("Daily challenge") + " " + day + "\n" + d.c + " " + d.m + " " + d.r + "/" + d.n + "\nhttps://openwineatlas.com";
  if (navigator.share) navigator.share({ text }).catch(() => {});
  else if (navigator.clipboard) navigator.clipboard.writeText(text).then(() => O.toast(t_("Copied. Paste it anywhere."))).catch(() => O.toast(text));
  else O.toast(text);
}
// a curated card back to a question, for the review
function curatedFromKey(p) {
  const l = DATA.byLesson.get(p[1]), i = +p[2];
  if (!l) return null;
  if (p[0] === "o" && l.odd && l.odd[i]) { const x = l.odd[i], order = shuffle([0, 1, 2, 3]); return { key: p.join(":"), kind: "mc", q: x.q || t_("Which one does not belong?"), options: order.map((k) => x.items[k]), answer: order.indexOf(x.odd), explain: x.why, from: l.title }; }
  if (p[0] === "x" && l.pairs && l.pairs[i]) return { key: p.join(":"), kind: "pairs", q: l.pairs[i].title, pairs: l.pairs[i].pairs.slice(), from: l.title };
  if (p[0] === "r" && l.order && l.order[i]) return { key: p.join(":"), kind: "order", q: l.order[i].title, items: l.order[i].items.slice(), explain: l.order[i].why, from: l.title };
  return null;
}
async function play(gid, theme) {
  const back = Object.assign({}, VIEW), g = GAME.get(gid);
  if (gid === "daily") {
    const day = dayStr();
    if (dailyDone(day)) { dailyShare(day); return; }
    if (!member() && leftToday() < 5) { O.toast(t_("The daily challenge takes 5 free questions, and fewer are left today. They come back tomorrow.")); return; }
    O.toast(t_("Preparing your questions…"));
    try {
      const { ctx, qs } = await dailyQs(day);
      if (qs.length < 5) { O.toast(t_("Not enough data here for a quiz yet. Try a larger region.")); return; }
      start(t_("Daily challenge") + " · " + ctx.label, qs, back, { game: "daily", day, country: ctx.label });
    } catch (e) { console.warn("daily", e); O.toast(t_("The questions could not be loaded right now.")); }
    return;
  }
  if (leftToday() <= 0) { VIEW = Object.assign({}, VIEW, { pay: true }); O.renderDash(); return; }
  O.toast(t_("Preparing your questions…"));
  try {
    const ctx = await themeCtx(theme || getTheme());
    if (gid === "where") await loadGameWines();
    const qs = buildGame(gid, ctx, g.n);
    start(t_(g.name) + " · " + ctx.label, qs.slice(0, member() ? qs.length : Math.min(qs.length, Math.max(leftToday(), 1))), back, { game: gid, theme: theme || getTheme() });
  } catch (e) { console.warn("game", e); O.toast(t_("The questions could not be loaded right now.")); }
}

// ---------- the pin on the map
const PIN = "qz-pin";
function pinData(features) {
  const map = O.map; if (!map) return;
  const data = { type: "FeatureCollection", features };
  if (map.getSource(PIN)) { map.getSource(PIN).setData(data); return; }
  if (!features.length) return;
  map.addSource(PIN, { type: "geojson", data });
  map.addLayer({ id: PIN + "-line", type: "line", source: PIN, filter: ["==", ["geometry-type"], "LineString"], paint: { "line-color": "#e7c06a", "line-width": 1.6, "line-dasharray": [2, 2] } });
  map.addLayer({ id: PIN + "-dot", type: "circle", source: PIN, filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 7, "circle-color": "#e7c06a", "circle-stroke-color": "#17130b", "circle-stroke-width": 2 } });
}
const pinClear = () => { try { pinData([]); } catch (e) {} };
function pinAnswer(e) {
  const q = QZ.qs[QZ.i], r = O.byId.get(q.place); if (!r || !e.lngLat) return;
  const p = [e.lngLat.lng, e.lngLat.lat], ids = O.placesAt(e.point);
  const inside = ids.includes(q.place) || ids.some((id) => O.pathOf(id).includes(q.place));
  const b = r[6], near = [Math.min(Math.max(p[0], b[0]), b[2]), Math.min(Math.max(p[1], b[1]), b[3])];
  const d = inside ? 0 : Math.max(0.3, km(p, near));
  const tol = Math.max(1, q.diag * 0.03), pts = inside ? 100 : Math.max(0, Math.round(100 * (1 - d / (q.diag * 0.5))));
  const feats = [{ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: p } }];
  if (!inside) feats.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [p, near] } });
  pinData(feats);
  const note = inside ? t_("Inside it.") : t_("{km} km away.", { km: O.fmtN(d < 10 ? Math.round(d * 10) / 10 : Math.round(d), 1) });
  answer(inside || d <= tol, -1, { pts, grade: inside ? 2 : d <= tol ? 1 : 0, note });
}

// ---------- the Study tab in My atlas
let VIEW = { path: null, lesson: null, pay: false };
function render() {
  if (!DATA) {
    loadData().then(() => O.renderDash()).catch(() => { const b = $("dashBody"); if (b) b.innerHTML = '<p class="lead">' + t_("The lessons could not be loaded right now.") + "</p>"; });
    return '<p class="lead">' + t_("Loading…") + "</p>";
  }
  if (VIEW.lesson && DATA.byLesson.has(VIEW.lesson)) return lessonView(DATA.byLesson.get(VIEW.lesson));
  if (VIEW.path && DATA.byPath.has(VIEW.path)) return pathView(DATA.byPath.get(VIEW.path));
  return hub();
}
function statusLine() {
  const s = ST().stats, acc = s.answered ? Math.round(100 * s.right / s.answered) : null, st = streak();
  return '<div class="st-stats">' +
    '<div class="tile"><b>' + O.fmtN(s.answered) + "</b><span>" + t_("questions answered") + "</span></div>" +
    '<div class="tile"><b>' + (acc == null ? "–" : acc + " %") + "</b><span>" + t_("right") + "</span></div>" +
    '<div class="tile"><b>' + st + "</b><span>" + (st === 1 ? t_("day in a row") : t_("days in a row")) + "</span></div>" +
    '<div class="tile"><b>' + (member() ? "∞" : leftToday()) + "</b><span>" + (member() ? t_("questions today, member") : t_("free questions left today")) + "</span></div></div>";
}
// the games, over the chosen theme
function themeOptions(cur) {
  const o = (v, label) => '<option value="' + esc(v) + '"' + (v === cur ? " selected" : "") + ">" + esc(label) + "</option>";
  const T = O.TREE && O.TREE.nodes ? O.TREE.nodes : {};
  const ccs = Object.keys(T).filter((k) => /^g:[A-Z]{2}$/.test(k) && (O.kidsOf(k) || []).length).sort((a, b) => nameOf(a).localeCompare(nameOf(b)));
  const DEEP = new Set(["g:FR", "g:IT", "g:ES", "g:PT", "g:DE", "g:AT", "g:US", "g:AU"]);
  const regions = ccs.map((k) => o("region:" + k, nameOf(k)) + (DEEP.has(k) ? (O.kidsOf(k) || []).filter((c) => /^g:/.test(c)).map((c) => o("region:" + c, "\u00a0\u00a0" + nameOf(c))).join("") : "")).join("");
  return o("all", t_("Everything, a new country each round")) +
    '<optgroup label="' + esc(t_("Study paths")) + '">' + DATA.paths.map((p) => o("path:" + p.id, p.title)).join("") + "</optgroup>" +
    '<optgroup label="' + esc(t_("Levels")) + '">' + LEVELS.map((l) => o("level:" + l, t_(l))).join("") + "</optgroup>" +
    '<optgroup label="' + esc(t_("Regions")) + '">' + regions + "</optgroup>" +
    '<optgroup label="' + esc(t_("Grapes")) + '">' + Object.keys(GRAPES).sort((a, b) => a.localeCompare(b)).map((g) => o("grape:" + g, g)).join("") + "</optgroup>";
}
function playHtml() {
  const day = dayStr(), done = dailyDone(day);
  const daily = '<button class="st-game st-daily" data-st-game="daily"><i>☀</i><b>' + t_("Daily challenge") + "</b><span>" +
    (done ? t_("Today: {marks} {r}/{n}. Tap to share.", { marks: done.m, r: done.r, n: done.n }) : t_("Today: {country}. Five questions, the same for everyone. Share your score.", { country: nameOf(dailyCC(day)) })) + "</span></button>";
  return "<h3>" + t_("Play") + '</h3><label class="st-theme">' + t_("Theme") + ' <select id="st-theme">' + themeOptions(getTheme()) + "</select></label>" +
    '<div class="st-games">' + daily + GAMES.filter((g) => g.id !== "daily").map((g) =>
      '<button class="st-game" data-st-game="' + g.id + '"><i>' + g.icon + "</i><b>" + t_(g.name) + "</b><span>" + t_(g.desc) + "</span>" +
      ((ST().best || {})[g.id] ? '<small>' + t_("Best: {n}", { n: O.fmtN(ST().best[g.id]) }) + "</small>" : "") + "</button>").join("") + "</div>";
}
function hub() {
  const due = dueKeys().length, cards = Object.keys(ST().cards).length;
  return '<p class="lead">' + t_("Learn the wine regions of the world on the map. Read a lesson, then test yourself: where a place is, its grapes, its rank, its neighbours. What you miss comes back until you know it.") + "</p>" +
    statusLine() + (VIEW.pay ? paywallHtml() : "") +
    '<div class="st-review"><div><b>' + t_("Review") + "</b><span>" + (cards ? t_("{n} cards due today, out of {all}", { n: due, all: cards }) : t_("Every question you answer becomes a card here.")) + "</span></div>" +
    '<button class="primary" data-st="review"' + (due ? "" : " disabled") + ">" + t_("Start review") + "</button></div>" +
    playHtml() +
    "<h3>" + t_("Study paths") + '</h3><div class="st-paths">' + DATA.paths.map((p) => {
      const done = p.lessons.filter((l) => ST().done[l.id]).length;
      return '<button class="st-path" data-st-path="' + esc(p.id) + '"><b>' + esc(p.title) + "</b><span>" + esc(t_(p.level)) + " · " + t_("{n} lessons", { n: p.lessons.length }) + "</span>" +
        '<span class="st-prog"><i style="width:' + (100 * done / p.lessons.length).toFixed(0) + '%"></i></span><small>' + esc(p.summary) + "</small></button>";
    }).join("") + "</div>" +
    '<p class="note">' + t_("Lessons are written by the atlas editors and checked against the official rules. Drills are built from the atlas data.") + "</p>" +
    '<p class="note">' + t_("The levels are our own. As a guide, Intermediate suits students between WSET Level 2 and 3, Advanced suits Level 3 to Diploma. Open Wine Atlas is independent and is not affiliated with or endorsed by WSET, the Court of Master Sommeliers or the Institute of Masters of Wine.") + "</p>";
}
function pathView(p) {
  const scope = p.scope && p.scope.length;
  return '<div class="st-nav"><button class="mini-btn" data-st="hub">← ' + t_("All paths") + "</button></div>" +
    "<h3 class=\"st-title\">" + esc(p.title) + '</h3><p class="lead">' + esc(p.summary) + "</p>" +
    (scope ? '<div class="st-drills"><button class="primary" data-st-drill="' + esc(p.id) + '">' + t_("Region drill") + '</button><button class="mini-btn" data-st-map="' + esc(p.id) + '">' + t_("Map quiz") + "</button>" +
      '<span class="note">' + t_("Ten questions built from the atlas data of this path.") + "</span></div>" : "") +
    '<div class="st-playpath"><span>' + t_("Play this path") + "</span>" + GAMES.filter((g) => g.id !== "daily").map((g) => '<button class="mini-btn" data-st-game="' + g.id + '" data-st-theme="path:' + esc(p.id) + '">' + g.icon + " " + t_(g.name) + "</button>").join("") + "</div>" +
    '<ol class="st-lessons">' + p.lessons.map((l) => {
      const lock = !lessonFree(l), done = ST().done[l.id];
      return '<li><button data-st-lesson="' + esc(l.id) + '"' + (done ? ' class="done"' : "") + "><span>" + esc(l.title) + "</span><small>" +
        (done ? "✓ " + t_("done") : t_("{n} min", { n: l.minutes || 5 })) + " · " + t_("{n} questions", { n: l.questions.length }) + (lock ? " · " + t_("members") : "") + "</small></button></li>";
    }).join("") + "</ol>";
}
function lessonView(l) {
  const p = l.path, lock = !lessonFree(l);
  const chips = (ids) => (ids || []).filter((id) => O.byId.has(id)).map((id) => '<button class="mini-btn" data-go="' + esc(id) + '">' + esc(O.byId.get(id)[0]) + " ↗</button>").join("");
  const sec = (s) => "<h4>" + esc(s.h) + "</h4>" + (s.p || []).map((x) => "<p>" + esc(x) + "</p>").join("") + (s.places && s.places.length ? '<div class="row st-places">' + chips(s.places) + "</div>" : "");
  const i = p.lessons.indexOf(l), nextL = p.lessons[i + 1];
  return '<div class="st-nav"><button class="mini-btn" data-st-path="' + esc(p.id) + '">← ' + esc(p.title) + "</button></div>" +
    '<article class="st-lesson"><div class="eyebrow">' + esc(p.title) + " · " + t_("Lesson {n}", { n: i + 1 }) + "</div><h3 class=\"st-title\">" + esc(l.title) + "</h3>" +
    '<p class="lead">' + esc(l.intro || "") + "</p>" +
    (lock ? (l.sections[0] ? sec(l.sections[0]) : "") + '<div class="qz-pay"><b>' + t_("The rest of this lesson is for members.") + "</b><p>" +
        t_("The first lesson of every path is free. Members read every lesson and study without limits.") + " " +
        t_("Membership opens soon: reserve a Founding spot now, nothing to pay until then.") + '</p><a class="primary" href="/founding?from=lesson">' + t_("Reserve my Founding spot") + " →</a></div>"
      : l.sections.map(sec).join("") +
        (l.key && l.key.length ? '<div class="st-key"><b>' + t_("Remember") + "</b><ul>" + l.key.map((k) => "<li>" + esc(k) + "</li>").join("") + "</ul></div>" : "") +
        '<div class="st-drills"><button class="primary" data-st-quiz="' + esc(l.id) + '">' + t_("Quiz on this lesson") + " · " + l.questions.length + "</button>" +
        '<button class="mini-btn" data-st-done="' + esc(l.id) + '">' + (ST().done[l.id] ? "✓ " + t_("Read") : t_("Mark as read")) + "</button>" +
        (nextL ? '<button class="mini-btn" data-st-lesson="' + esc(nextL.id) + '">' + t_("Next lesson") + " →</button>" : "") + "</div>") +
    "</article>";
}
function wire() {
  const body = $("dashBody"); if (!body || body.dataset.stWired) return;
  body.dataset.stWired = "1";
  body.addEventListener("change", (e) => {
    if (e.target.id !== "st-theme") return;
    store.set(THEME_KEY, e.target.value);
    O.toast(t_("Theme: {name}", { name: e.target.selectedOptions[0] ? e.target.selectedOptions[0].textContent.trim() : "" }));
  });
  body.addEventListener("click", (e) => {
    if (!body.querySelector(".st-paths, .st-lessons, .st-lesson, .st-review")) return;
    const b = e.target.closest("[data-st], [data-st-path], [data-st-lesson], [data-st-quiz], [data-st-done], [data-st-drill], [data-st-map], [data-st-game]");
    if (!b) return;
    const d = b.dataset;
    if (d.stGame) return play(d.stGame, d.stTheme);
    if (d.st === "hub") { VIEW = { path: null, lesson: null }; }
    else if (d.st === "review") { const back = Object.assign({}, VIEW); return begin(t_("Review"), reviewQs, back); }
    else if (d.stPath) { VIEW = { path: d.stPath, lesson: null }; }
    else if (d.stLesson) { VIEW = { path: DATA.byLesson.get(d.stLesson).path.id, lesson: d.stLesson }; }
    else if (d.stDone) { const s = ST(); if (s.done[d.stDone]) delete s.done[d.stDone]; else s.done[d.stDone] = Date.now(); save(); }
    else if (d.stQuiz) {
      const l = DATA.byLesson.get(d.stQuiz), back = Object.assign({}, VIEW);
      if (!ST().done[l.id]) { ST().done[l.id] = Date.now(); save(); }
      return begin(l.title, async () => shuffle(l.questions.map((q) => lessonQ(l, q))), back);
    }
    else if (d.stDrill || d.stMap) {
      const p = DATA.byPath.get(d.stDrill || d.stMap), back = Object.assign({}, VIEW);
      return begin(p.title + " · " + (d.stMap ? t_("Map quiz") : t_("Region drill")), () => drillQs(p, d.stMap ? MAP_KINDS : ALL_KINDS), back);
    }
    O.renderDash();
    const db = $("dashBody"); if (db) db.scrollTop = 0;
  });
}

// ---------- styles
const css = document.createElement("style");
css.textContent = `
.quiz { position: fixed; z-index: 30; right: 16px; top: 16px; width: min(400px, calc(100vw - 32px)); max-height: calc(100vh - 32px); overflow: auto;
  background: var(--panel, #141418); border: 1px solid var(--line, #2a2a31); border-radius: 14px; padding: 14px 16px 16px; box-shadow: 0 10px 40px rgba(0,0,0,.45);
  backdrop-filter: blur(12px); color: var(--parchment, #e6dccb); font: 14px/1.5 var(--f-body, sans-serif); }
@media (max-width: 760px) { .quiz { left: 8px; right: 8px; top: auto; bottom: 8px; width: auto; max-height: 52vh; border-radius: 16px; } }
.qz-h { display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--muted, #8d877c); }
.qz-t { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; letter-spacing: .04em; text-transform: uppercase; font-family: var(--f-mono, monospace); }
.qz-n { font-family: var(--f-mono, monospace); }
.qz-x { background: none; border: 0; color: inherit; font-size: 16px; cursor: pointer; padding: 4px 6px; }
.qz-bar { height: 3px; background: var(--line, #2a2a31); border-radius: 2px; margin: 8px 0 12px; overflow: hidden; }
.qz-bar i { display: block; height: 100%; background: var(--gold, #e7c06a); transition: width .3s; }
.qz-q { font: 500 20px/1.3 var(--f-display, serif); margin: 0 0 12px; }
.qz-hint { margin: -4px 0 10px; color: var(--muted, #8d877c); font-size: 13px; }
.qz-o { display: grid; gap: 8px; }
.qz-o button, .qz-row button, .qz-row a, .qz-pay a, .st-drills .primary, .st-review .primary { text-align: left; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--line, #2a2a31);
  background: #1b1b20; color: inherit; font: inherit; cursor: pointer; text-decoration: none; }
.qz-o button:hover:not(:disabled) { border-color: #6b5a33; }
.qz-o button.right { border-color: #6f9d5a; background: #1d2a18; }
.qz-o button.wrong { border-color: #b45f4f; background: #2c1a17; }
.qz-o button.ghost, .qz-row .ghost { background: none; color: var(--muted, #8d877c); }
.qz-f { margin-top: 12px; padding: 10px 12px; border-radius: 10px; border-left: 3px solid var(--line, #2a2a31); background: #18181c; font-size: 13.5px; }
.qz-f.ok { border-left-color: #6f9d5a; } .qz-f.no { border-left-color: #b45f4f; }
.qz-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.qz-row .primary, .qz-pay .primary, .st-drills .primary, .st-review .primary { background: var(--gold, #e7c06a); color: #17130b; border-color: transparent; font-weight: 600; }
.st-review .primary:disabled { opacity: .45; cursor: default; }
.qz-end { display: grid; gap: 4px; margin: 14px 0 6px; } .qz-end b { font: 600 40px/1 var(--f-display, serif); color: var(--gold, #e7c06a); }
.qz-pay { margin: 12px 0; padding: 14px; border: 1px solid #5a4a2a; border-radius: 12px; background: #1c1810; display: grid; gap: 6px; }
.qz-pay p { margin: 0; color: #cfc6b6; font-size: 13.5px; } .qz-pay a { justify-self: start; margin-top: 4px; }
.st-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; margin: 14px 0; }
.st-review { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding: 14px; border: 1px solid var(--line); border-radius: 12px; margin-bottom: 18px; }
.st-review div { display: grid; } .st-review span { color: var(--muted); font-size: 12.5px; }
.st-paths { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; }
.st-path { text-align: left; display: grid; gap: 4px; padding: 14px; border: 1px solid var(--line); border-radius: 12px; background: #17171b; color: inherit; font: inherit; cursor: pointer; }
.st-path:hover { border-color: #57534a; } .st-path b { font: 600 20px/1.15 var(--f-display); } .st-path span, .st-path small { color: var(--muted); font-size: 12px; } .st-path small { line-height: 1.4; }
.st-prog { height: 3px; background: var(--line); border-radius: 2px; overflow: hidden; margin: 4px 0; } .st-prog i { display: block; height: 100%; background: var(--gold); }
.st-nav { margin-bottom: 8px; } .st-title { font: 600 28px/1.15 var(--f-display); margin: 6px 0 8px; }
.st-drills { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 14px 0; }
.st-lessons { list-style: none; padding: 0; margin: 10px 0; display: grid; gap: 6px; counter-reset: l; }
.st-lessons button { width: 100%; text-align: left; display: grid; gap: 2px; padding: 12px 14px; border: 1px solid var(--line); border-radius: 10px; background: #17171b; color: inherit; font: inherit; cursor: pointer; }
.st-lessons button span { font-weight: 500; } .st-lessons button small { color: var(--muted); font-size: 12px; } .st-lessons button.done small { color: #8fb47a; }
.st-lesson { max-width: 680px; } .st-lesson h4 { font: 600 15px var(--f-body); margin: 22px 0 6px; } .st-lesson p { color: #d6cdbd; line-height: 1.65; margin: 0 0 10px; }
.st-places { margin: 6px 0 4px; }
.st-key { margin: 22px 0 8px; padding: 12px 14px; border-left: 3px solid var(--gold); background: #1a1712; border-radius: 0 10px 10px 0; }
.st-games { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin: 10px 0 22px; }
.st-game { position: relative; text-align: left; display: grid; gap: 4px; padding: 14px 14px 14px 52px; border: 1px solid var(--line); border-radius: 12px; background: #17171b; color: inherit; font: inherit; cursor: pointer; min-height: 84px; }
.st-game:hover { border-color: #6b5a33; }
.st-game i { position: absolute; left: 14px; top: 14px; width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center; font-style: normal; font-size: 15px; background: #241f15; color: var(--gold, #e7c06a); border: 1px solid #4a3d22; }
.st-game b { font: 600 17px/1.2 var(--f-display); } .st-game span { color: var(--muted); font-size: 12.5px; line-height: 1.4; } .st-game small { color: var(--gold, #e7c06a); font-size: 11.5px; font-family: var(--f-mono, monospace); }
.st-daily { grid-column: 1 / -1; background: linear-gradient(120deg, #221c10, #17171b 70%); border-color: #4a3d22; }
.st-daily b { font-size: 21px; }
.st-theme { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; flex-wrap: wrap; }
.st-theme select { flex: 1; min-width: 200px; max-width: 420px; padding: 8px 10px; border-radius: 10px; border: 1px solid var(--line); background: #17171b; color: inherit; font: inherit; }
.st-playpath { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin: 4px 0 12px; } .st-playpath span { color: var(--muted); font-size: 12.5px; margin-right: 4px; }
.qz-sub { margin: -6px 0 12px; color: var(--gold, #e7c06a); font-size: 14px; }
.qz-clues { margin: 0 0 10px; padding-left: 20px; display: grid; gap: 5px; } .qz-clues li { color: #d6cdbd; } .qz-clues li.late { color: var(--muted, #8d877c); }
.qz-cluebar { align-items: center; justify-content: space-between; margin: 0 0 10px; } .qz-pts { color: var(--gold, #e7c06a); font-family: var(--f-mono, monospace); font-size: 12px; }
.qz-pick { list-style: decimal; margin: 0 0 8px; padding-left: 22px; display: grid; gap: 6px; min-height: 4px; }
.qz-pick button { width: 100%; text-align: left; padding: 8px 10px; border-radius: 10px; border: 1px solid #6b5a33; background: #221d12; color: inherit; font: inherit; cursor: pointer; }
.qz-sol { margin: 8px 0; padding-left: 22px; } .qz-sol li { color: #e2a397; } .qz-sol li.ok { color: #9fcb8a; }
.qz-pairs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; } .qz-pairs > div { display: grid; gap: 6px; align-content: start; }
.qz-pairs button { text-align: left; padding: 9px 10px; border-radius: 10px; border: 1px solid var(--line, #2a2a31); background: #1b1b20; color: inherit; font: inherit; font-size: 13px; cursor: pointer; transition: border-color .15s, background .15s; }
.qz-pairs button.sel { border-color: var(--gold, #e7c06a); background: #241f15; } .qz-pairs button.right { border-color: #6f9d5a; background: #1d2a18; } .qz-pairs button.wrong { border-color: #b45f4f; background: #2c1a17; }
.qz-note { margin: 8px 0 0; color: #bdb4a4; font-size: 12.5px; font-style: italic; }
.qz-marks { font-size: 26px; letter-spacing: 3px; margin: 6px 0 0; } .qz-ptsline { color: var(--gold, #e7c06a); font-family: var(--f-mono, monospace); margin: 4px 0 0; }
.st-key ul { margin: 6px 0 0; padding-left: 18px; } .st-key li { margin: 3px 0; color: #d6cdbd; }
`;
document.head.appendChild(css);

window.OWA_STUDY = { render, wire, loadData, member };
loadData().catch(() => {});
})();
