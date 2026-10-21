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
async function start(title, qs, back) {
  if (!qs.length) { O.toast(t_("Not enough data here for a quiz yet. Try a larger region.")); return; }
  QZ = { title, qs, i: 0, right: 0, missed: [], back, answered: false };
  O.closeDash();
  card().hidden = false;
  window.OWA_QUIZ_CLICK = onMapClick;
  show();
}
function stop(toStudy) {
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
  O.quizMode(q.map === "find" ? "find" : true);
  O.clearSelected();
  const head = '<div class="qz-h"><span class="qz-t">' + esc(QZ.title) + '</span><span class="qz-n">' + (QZ.i + 1) + " / " + QZ.qs.length + '</span><button class="qz-x" data-qz="close" aria-label="' + t_("Close the quiz") + '">✕</button></div>' +
    '<div class="qz-bar"><i style="width:' + (100 * QZ.i / QZ.qs.length).toFixed(1) + '%"></i></div>';
  let body = '<p class="qz-q">' + esc(q.q) + "</p>";
  if (q.kind === "mc") body += '<div class="qz-o">' + q.options.map((o, i) => '<button data-opt="' + i + '">' + esc(o) + "</button>").join("") + "</div>";
  else body += '<p class="qz-hint">' + t_("Tap the place on the map.") + '</p><div class="qz-o"><button data-qz="giveup" class="ghost">' + t_("Show me") + "</button></div>";
  el.innerHTML = head + body + '<div class="qz-f" id="qz-f" hidden></div>';
  // the map: an outlined place for "identify", the area around for "find", the place itself for other questions about a place
  if (q.map) {
    const b = frameFor(q); if (b) O.fitTo(b, "appellation");
    if (q.map === "identify") setTimeout(() => O.markSelected(q.place), 50);
  }
}
function answer(ok, chosen) {
  if (QZ.answered) return;
  QZ.answered = true;
  const q = QZ.qs[QZ.i], el = card();
  countAnswer(q.key, ok);
  if (ok) QZ.right++; else QZ.missed.push(q.key);
  el.querySelectorAll("[data-opt]").forEach((b) => {
    const i = +b.dataset.opt; b.disabled = true;
    if (i === q.answer) b.classList.add("right"); else if (i === chosen) b.classList.add("wrong");
  });
  const gu = el.querySelector('[data-qz="giveup"]'); if (gu) gu.remove();
  O.quizMode(true);
  if (q.place) { O.markSelected(q.place); const r = O.byId.get(q.place); if (r && q.map !== "identify" && isArea(r)) O.fitTo(frameFor(q) || r[6], r[3]); }
  const name = q.place ? (O.byId.get(q.place) || [""])[0] : "";
  const f = $("qz-f");
  f.hidden = false;
  f.className = "qz-f " + (ok ? "ok" : "no");
  const last = QZ.i === QZ.qs.length - 1;
  f.innerHTML = '<b>' + (ok ? t_("Right.") : q.kind === "find" ? t_("Here it is.") : t_("Not quite.")) + "</b> " + (q.explain ? esc(q.explain) : "") +
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
  O.quizMode(true); O.clearSelected();
  const el = card(), n = QZ.qs.length, pct = Math.round(100 * QZ.right / n);
  el.innerHTML = '<div class="qz-h"><span class="qz-t">' + esc(QZ.title) + '</span><button class="qz-x" data-qz="close" aria-label="' + t_("Close the quiz") + '">✕</button></div>' +
    '<div class="qz-end"><b>' + QZ.right + " / " + n + "</b><span>" + (pct >= 90 ? t_("Excellent.") : pct >= 70 ? t_("Well done.") : pct >= 50 ? t_("Good start. The misses come back in your review.") : t_("Keep going. The misses come back in your review.")) + "</span></div>" +
    '<div class="qz-row">' + (QZ.missed.length ? '<button class="primary" data-qz="missed">' + t_("Try the {n} misses again", { n: QZ.missed.length }) + "</button>" : "") +
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
  if (q.kind !== "find") return;
  const ids = O.placesAt(e.point);
  const ok = ids.includes(q.place) || ids.some((id) => O.pathOf(id).includes(q.place));
  if (!ids.length) return O.toast(t_("Tap inside an outline."));
  answer(ok, -1);
}
document.addEventListener("click", (e) => {
  const o = e.target.closest("#quiz [data-opt]");
  if (o && QZ && !QZ.answered) { const i = +o.dataset.opt; return answer(i === QZ.qs[QZ.i].answer, i); }
  const b = e.target.closest("#quiz [data-qz]");
  if (!b || !QZ) return;
  const a = b.dataset.qz;
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
  if (!QZ.answered && q && q.kind === "mc" && /^[1-4]$/.test(e.key) && +e.key <= q.options.length) { e.preventDefault(); answer(+e.key - 1 === q.answer, +e.key - 1); }
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
function hub() {
  const due = dueKeys().length, cards = Object.keys(ST().cards).length;
  return '<p class="lead">' + t_("Learn the wine regions of the world on the map. Read a lesson, then test yourself: where a place is, its grapes, its rank, its neighbours. What you miss comes back until you know it.") + "</p>" +
    statusLine() + (VIEW.pay ? paywallHtml() : "") +
    '<div class="st-review"><div><b>' + t_("Review") + "</b><span>" + (cards ? t_("{n} cards due today, out of {all}", { n: due, all: cards }) : t_("Every question you answer becomes a card here.")) + "</span></div>" +
    '<button class="primary" data-st="review"' + (due ? "" : " disabled") + ">" + t_("Start review") + "</button></div>" +
    "<h3>" + t_("Study paths") + '</h3><div class="st-paths">' + DATA.paths.map((p) => {
      const done = p.lessons.filter((l) => ST().done[l.id]).length;
      return '<button class="st-path" data-st-path="' + esc(p.id) + '"><b>' + esc(p.title) + "</b><span>" + esc(p.level) + " · " + t_("{n} lessons", { n: p.lessons.length }) + "</span>" +
        '<span class="st-prog"><i style="width:' + (100 * done / p.lessons.length).toFixed(0) + '%"></i></span><small>' + esc(p.summary) + "</small></button>";
    }).join("") + "</div>" +
    '<p class="note">' + t_("Lessons are written by the atlas editors and checked against the official rules. Drills are built from the atlas data.") + "</p>";
}
function pathView(p) {
  const scope = p.scope && p.scope.length;
  return '<div class="st-nav"><button class="mini-btn" data-st="hub">← ' + t_("All paths") + "</button></div>" +
    "<h3 class=\"st-title\">" + esc(p.title) + '</h3><p class="lead">' + esc(p.summary) + "</p>" +
    (scope ? '<div class="st-drills"><button class="primary" data-st-drill="' + esc(p.id) + '">' + t_("Region drill") + '</button><button class="mini-btn" data-st-map="' + esc(p.id) + '">' + t_("Map quiz") + "</button>" +
      '<span class="note">' + t_("Ten questions built from the atlas data of this path.") + "</span></div>" : "") +
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
  body.addEventListener("click", (e) => {
    if (!body.querySelector(".st-paths, .st-lessons, .st-lesson, .st-review")) return;
    const b = e.target.closest("[data-st], [data-st-path], [data-st-lesson], [data-st-quiz], [data-st-done], [data-st-drill], [data-st-map]");
    if (!b) return;
    const d = b.dataset;
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
.st-key ul { margin: 6px 0 0; padding-left: 18px; } .st-key li { margin: 3px 0; color: #d6cdbd; }
`;
document.head.appendChild(css);

window.OWA_STUDY = { render, wire, loadData, member };
loadData().catch(() => {});
})();
