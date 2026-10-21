// Open Wine Atlas: study and quiz (web only).
//
// Paths of lessons (web/data/study.json, written by people, checked against the atlas) and quizzes:
//   lesson quiz    the questions written for a lesson
//   region drill   questions built from the atlas data of a region: where it is, its grape, its rank, its parent,
//                  which lies highest, its state or commune
//   map quiz       only the map questions: name the outlined place, or find a place on the map
//   review         spaced repetition: every question answered becomes a card; a miss comes back tomorrow,
//                  a right answer later and later (Leitner boxes)
//   flashcards     the "cards" of each lesson (front, back, an optional atlas place): a deck per lesson and per path;
//                  a card marked Again goes into the review like a missed question (key f:<lesson id>:<hash of the front>)
//   mock exam      thirty questions drawn from all the lessons of a path, scored at the end, optional time limit
// Free: the first lesson of each path (its reading, quiz and cards), FREE_PER_DAY answers a day and a sample exam of
// SAMPLE_N questions per path. Members: everything.
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
const EXAM_N = 30, SAMPLE_N = 10, PASS = 70, MIN_PER_Q = 1.5; // 30 questions, 45 minutes

// ---------- state
// last: the lesson opened last, for "Continue" on the Home of My atlas
function blank() { return { cards: {}, done: {}, stats: { answered: 0, right: 0, days: [], flips: 0 }, today: { d: "", n: 0 }, last: null }; }
// MY.study can be replaced by a sync from another device: fill in whatever is missing each time
function norm(s) {
  const b = blank();
  if (!s || typeof s !== "object") return b;
  return { cards: s.cards || {}, done: s.done || {}, stats: Object.assign(b.stats, s.stats || {}), today: Object.assign(b.today, s.today || {}), last: s.last || null };
}
function loadState() {
  let s = null;
  try { s = JSON.parse(store.get("study") || "null"); } catch (e) {}
  return norm(s);
}
MY.study = norm(MY.study && Object.keys(MY.study).length ? MY.study : loadState());
const ST = () => { const s = MY.study; if (!s || !s.cards || !s.done || !s.stats || !s.today) MY.study = norm(s); return MY.study; };
const save = () => O.saveMY("study");
const dayStr = (t = Date.now()) => { const d = new Date(t); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const member = () => !!(window.OWA_ACCOUNT && window.OWA_ACCOUNT.member && window.OWA_ACCOUNT.member()) || store.get("member") === "1";
function usedToday() { const t = ST().today; return t.d === dayStr() ? t.n : 0; }
const leftToday = () => member() ? Infinity : Math.max(0, FREE_PER_DAY - usedToday());
// opt.free: not counted in the free answers of the day (mock exam, flashcards)
// opt.flash: a flashcard; "Got it" moves a card that is already in the review, "Again" puts it there
function countAnswer(key, ok, opt = {}) {
  const s = ST(), today = dayStr();
  if (!opt.free && !opt.flash) {
    if (s.today.d !== today) s.today = { d: today, n: 0 };
    s.today.n++;
  }
  if (opt.flash) s.stats.flips = (s.stats.flips || 0) + 1;
  else { s.stats.answered++; if (ok) s.stats.right++; }
  if (s.stats.days[s.stats.days.length - 1] !== today) { s.stats.days.push(today); if (s.stats.days.length > 400) s.stats.days = s.stats.days.slice(-400); }
  if (opt.flash && ok && !s.cards[key]) { save(); return; }
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
    DATA.byLesson = new Map(); DATA.byPath = new Map(); DATA.byCard = new Map();
    d.paths.forEach((p) => {
      p.scope = Array.isArray(p.scope) ? p.scope : [];
      DATA.byPath.set(p.id, p);
      p.lessons.forEach((l, i) => {
        l.path = p; l.n = i; DATA.byLesson.set(l.id, l);
        l.questions = l.questions || [];
        l.cards = (Array.isArray(l.cards) ? l.cards : []).filter((c) => c && c.f && c.b);
        l.cards.forEach((c) => { c.key = "f:" + l.id + ":" + hash(c.f); c.lesson = l; DATA.byCard.set(c.key, c); });
      });
    });
    return DATA;
  }).catch((e) => { loading = null; throw e; });
  return loading;
}
const lessonFree = (l) => l.n === 0 || member();
// a short stable name for a card: its front text (a card keeps its place in the review when cards are added or moved)
function hash(x) { let h = 0x811c9dc5; for (let i = 0; i < x.length; i++) { h ^= x.charCodeAt(i); h = Math.imul(h, 0x01000193); } return (h >>> 0).toString(36); }
const cardsOf = (p) => p.lessons.reduce((n, l) => n + l.cards.length, 0);

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
// a card key back to a question: lesson questions as written, data questions built again with fresh options,
// flashcards as they are
async function fromKey(key) {
  const p = key.split(":");
  if (p[0] === "f") {
    await loadData();
    const c = DATA.byCard.get(key);
    return c ? flashQ(c) : null;
  }
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
const flashQ = (c) => ({ key: c.key, kind: "flash", q: c.f, back: c.b, place: c.place && O.byId.has(c.place) ? c.place : null, from: c.lesson.title });
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
  QZ.answered = false; QZ.revealed = false;
  O.quizMode(q.map === "find" ? "find" : true);
  O.clearSelected();
  const head = '<div class="qz-h"><span class="qz-t">' + esc(QZ.title) + '</span><span class="qz-n">' + (QZ.i + 1) + " / " + QZ.qs.length + '</span><button class="qz-x" data-qz="close" aria-label="' + t_("Close the quiz") + '">✕</button></div>' +
    '<div class="qz-bar"><i style="width:' + (100 * QZ.i / QZ.qs.length).toFixed(1) + '%"></i></div>';
  let body = (q.kind === "flash" ? '<p class="qz-hint qz-kind">' + t_("Flashcard") + (q.from ? " · " + esc(q.from) : "") + "</p>" : "") + '<p class="qz-q">' + esc(q.q) + "</p>";
  if (q.kind === "mc") body += '<div class="qz-o">' + q.options.map((o, i) => '<button data-opt="' + i + '">' + esc(o) + "</button>").join("") + "</div>";
  else if (q.kind === "flash") body += '<div class="qz-o" id="qz-flash"><button class="qz-reveal" data-qz="reveal">' + t_("Show the answer") + ' <kbd>Space</kbd></button></div>';
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
// a flashcard in the review: turn it, then say whether you knew it
function reveal() {
  const q = QZ && QZ.qs[QZ.i];
  if (!q || q.kind !== "flash" || QZ.revealed) return;
  QZ.revealed = true;
  const box = $("qz-flash"); if (!box) return;
  box.outerHTML = '<div class="qz-back">' + esc(q.back) + '</div><div class="qz-o qz-grade" role="group" aria-label="' + esc(t_("Did you know it?")) + '">' +
    '<button class="fc-again" data-qz="again">' + t_("Again") + " <kbd>1</kbd></button>" + '<button class="fc-got" data-qz="got">' + t_("Got it") + " <kbd>2</kbd></button></div>";
  if (q.place) { O.markSelected(q.place); const r = O.byId.get(q.place); if (r && isArea(r)) O.fitTo(frameFor(q) || r[6], r[3]); }
  const g = card().querySelector('[data-qz="got"]'); if (g) g.focus();
}
function grade(ok) {
  const q = QZ && QZ.qs[QZ.i];
  if (!q || QZ.answered) return;
  QZ.answered = true;
  countAnswer(q.key, ok, { flash: true });
  if (ok) QZ.right++; else QZ.missed.push(q.key);
  next();
}
function next() {
  if (QZ.i < QZ.qs.length - 1) {
    if (leftToday() <= 0 && QZ.qs[QZ.i + 1].kind !== "flash") return paywall();
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
  else if (a === "reveal") reveal();
  else if (a === "again") grade(false);
  else if (a === "got") grade(true);
  else if (a === "study") stop(true);
  else if (a === "open") { const r = O.byId.get(b.dataset.id); stop(false); if (r) O.goTo(r); }
});
document.addEventListener("keydown", (e) => {
  if (!QZ || $("quiz")?.hidden) return;
  if (e.key === "Escape") { stop(true); return; }
  if (e.target.closest("input, textarea")) return;
  const q = QZ.qs[QZ.i];
  if (q && q.kind === "flash" && !QZ.answered) {
    if (!QZ.revealed && (e.key === " " || e.key === "Enter")) { if (e.target.closest("button")) return; e.preventDefault(); reveal(); }
    else if (QZ.revealed && (e.key === "1" || e.key === "2")) { e.preventDefault(); grade(e.key === "2"); }
    return;
  }
  if (!QZ.answered && q && q.kind === "mc" && /^[1-4]$/.test(e.key) && +e.key <= q.options.length) { e.preventDefault(); answer(+e.key - 1 === q.answer, +e.key - 1); }
  else if (QZ.answered && e.key === "Enter") { e.preventDefault(); next(); }
});

// ---------- launching
async function begin(title, make, back) {
  if (leftToday() <= 0) { VIEW = Object.assign({}, VIEW, { pay: true }); O.openDash("study"); return; }
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

// ---------- the Study, Flashcards and Mock exam sections of My atlas
let VIEW = { path: null, lesson: null, pay: false };
let FC = null;      // the flashcard deck under way
let FCPAY = null;   // a deck for members was asked for: the lesson whose cards are free instead
let EX = null;      // the mock exam under way, or its result
let PICK = null;    // the path a mock exam link asked for
let FOCUS = null;   // what gets the focus after the next render
const mmss = (ms) => { const s = Math.max(0, Math.ceil(ms / 1000)); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); };
function render(mode) {
  if (!DATA) {
    loadData().then(() => O.renderDash()).catch(() => { const b = $("dashBody"); if (b) b.insertAdjacentHTML("beforeend", '<p class="lead">' + t_("The lessons could not be loaded right now.") + "</p>"); });
    return '<p class="lead">' + t_("Loading…") + "</p>";
  }
  let html;
  if (mode === "cards") html = FC ? deckView() : cardsHub();
  else if (mode === "exam") html = !EX ? examHub() : EX.done ? examResult() : examView();
  else if (VIEW.lesson && DATA.byLesson.has(VIEW.lesson)) html = lessonView(DATA.byLesson.get(VIEW.lesson));
  else if (VIEW.path && DATA.byPath.has(VIEW.path)) html = pathView(DATA.byPath.get(VIEW.path));
  else html = hub();
  return '<div class="st">' + html + "</div>";
}
function markLast(l) { const s = ST(); s.last = { id: l.id, t: l.title, p: l.path.title, at: Date.now() }; save(); }
function statusLine() {
  const s = ST().stats, acc = s.answered ? Math.round(100 * s.right / s.answered) : null, st = streak();
  return '<div class="st-stats">' +
    '<div class="tile"><b>' + O.fmtN(s.answered) + "</b><span>" + t_("questions answered") + "</span></div>" +
    '<div class="tile"><b>' + (acc == null ? "–" : acc + " %") + "</b><span>" + t_("right") + "</span></div>" +
    '<div class="tile"><b>' + st + "</b><span>" + (st === 1 ? t_("day in a row") : t_("days in a row")) + "</span></div>" +
    '<div class="tile"><b>' + (member() ? "∞" : leftToday()) + "</b><span>" + (member() ? t_("questions today, member") : t_("free questions left today")) + "</span></div></div>";
}
function reviewRow() {
  const due = dueKeys().length, cards = Object.keys(ST().cards).length;
  return '<div class="st-review"><div><b>' + t_("Review") + "</b><span>" + (cards ? t_("{n} cards due today, out of {all}", { n: due, all: cards }) : t_("Every question you answer, and every flashcard you mark Again, comes back here.")) + "</span></div>" +
    '<button class="primary" data-st="review"' + (due ? "" : " disabled") + ">" + t_("Start review") + "</button></div>";
}
function hub() {
  const nc = DATA.paths.reduce((n, p) => n + cardsOf(p), 0);
  return '<p class="lead">' + t_("Learn the wine regions of the world on the map. Read a lesson, then test yourself: where a place is, its grapes, its rank, its neighbours. What you miss comes back until you know it.") + "</p>" +
    statusLine() + (VIEW.pay ? paywallHtml() : "") + reviewRow() +
    '<div class="st-modes"><button data-st-tab="cards">' + O.icon("cards", 18) + "<b>" + t_("Flashcards") + "</b><span>" +
      (nc ? t_("{n} cards: turn a card, say the answer, see if you knew it.", { n: O.fmtN(nc) }) : t_("Turn a card, say the answer, see if you knew it.")) + "</span></button>" +
    '<button data-st-tab="exam">' + O.icon("exam", 18) + "<b>" + t_("Mock exam") + "</b><span>" + t_("Thirty questions from a whole path, no help until the end, then your score.") + "</span></button></div>" +
    "<h3>" + t_("Study paths") + '</h3><div class="st-paths">' + DATA.paths.map((p) => {
      const done = p.lessons.filter((l) => ST().done[l.id]).length;
      return '<button class="st-path" data-st-path="' + esc(p.id) + '"><b>' + esc(p.title) + "</b><span>" + esc(p.level) + " · " + t_("{n} lessons", { n: p.lessons.length }) + "</span>" +
        '<span class="st-prog"><i style="width:' + (100 * done / Math.max(1, p.lessons.length)).toFixed(0) + '%"></i></span><small>' + esc(p.summary) + "</small></button>";
    }).join("") + "</div>" +
    '<p class="note">' + t_("Lessons are written by the atlas editors and checked against the official rules. Drills are built from the atlas data.") + "</p>";
}
function pathView(p) {
  const scope = p.scope && p.scope.length, nc = cardsOf(p), nq = p.lessons.reduce((n, l) => n + l.questions.length, 0);
  return '<div class="st-nav"><button class="mini-btn" data-st="hub">← ' + t_("All paths") + "</button></div>" +
    "<h3 class=\"st-title\">" + esc(p.title) + '</h3><p class="lead">' + esc(p.summary) + "</p>" +
    '<div class="st-drills">' +
      (scope ? '<button class="primary" data-st-drill="' + esc(p.id) + '">' + t_("Region drill") + '</button><button class="mini-btn" data-st-map="' + esc(p.id) + '">' + t_("Map quiz") + "</button>" : "") +
      (nc ? '<button class="mini-btn" data-st-deck="path:' + esc(p.id) + '">' + t_("All cards of this path") + " · " + nc + "</button>" : "") +
      (nq ? '<button class="mini-btn" data-ex-go="' + esc(p.id) + '">' + t_("Mock exam") + "</button>" : "") +
      (scope ? '<span class="note">' + t_("Ten questions built from the atlas data of this path.") + "</span>" : '<span class="note">' + t_("Theory only: no map drills for this path.") + "</span>") + "</div>" +
    '<ol class="st-lessons">' + p.lessons.map((l) => {
      const lock = !lessonFree(l), done = ST().done[l.id];
      return '<li><button class="st-lb' + (done ? " done" : "") + '" data-st-lesson="' + esc(l.id) + '"><span>' + esc(l.title) + "</span><small>" +
        (done ? "✓ " + t_("done") : t_("{n} min", { n: l.minutes || 5 })) + " · " + t_("{n} questions", { n: l.questions.length }) + (lock ? " · " + t_("members") : "") + "</small></button>" +
        (l.cards.length ? '<button class="mini-btn st-lc" data-st-deck="lesson:' + esc(l.id) + '" aria-label="' + esc(t_("Flashcards of {title}", { title: l.title })) + '">' + t_("{n} cards", { n: l.cards.length }) + "</button>" : "") + "</li>";
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
        '<div class="st-drills">' + (l.questions.length ? '<button class="primary" data-st-quiz="' + esc(l.id) + '">' + t_("Quiz on this lesson") + " · " + l.questions.length + "</button>" : "") +
        (l.cards.length ? '<button class="mini-btn" data-st-deck="lesson:' + esc(l.id) + '">' + t_("Flashcards") + " · " + l.cards.length + "</button>" : "") +
        '<button class="mini-btn" data-st-done="' + esc(l.id) + '">' + (ST().done[l.id] ? "✓ " + t_("Read") : t_("Mark as read")) + "</button>" +
        (nextL ? '<button class="mini-btn" data-st-lesson="' + esc(nextL.id) + '">' + t_("Next lesson") + " →</button>" : "") + "</div>") +
    "</article>";
}
function memberBox(title, from) {
  return '<div class="qz-pay"><b>' + title + "</b><p>" + t_("The first lesson of every path is free. Members read every lesson and study without limits.") + " " +
    t_("Membership opens soon: reserve a Founding spot now, nothing to pay until then.") + '</p><a class="primary" href="/founding?from=' + from + '">' + t_("Reserve my Founding spot") + " →</a></div>";
}

// ---------- flashcards
function cardsHub() {
  const paths = DATA.paths.filter((p) => cardsOf(p));
  const pay = FCPAY ? memberBox(t_("These cards are for members."), "cards") +
    (FCPAY.cards.length ? '<div class="row"><button class="mini-btn" data-st-deck="lesson:' + esc(FCPAY.id) + '">' + t_("Study the free cards: {title}", { title: esc(FCPAY.title) }) + "</button></div>" : "") : "";
  if (!paths.length) return pay + '<div class="empty">' + t_("The flashcards are being written. They come with the next update of the lessons.") + "</div>" + reviewRow();
  return pay + reviewRow() +
    '<p class="note">' + t_("Press Space or tap a card to turn it, then 1 for Again or 2 for Got it. A card you mark Again comes back in your review.") + "</p>" +
    paths.map((p) => '<section class="fc-path"><div class="fc-ph"><div><b>' + esc(p.title) + "</b><span>" + esc(p.level) + " · " + t_("{n} cards", { n: cardsOf(p) }) + "</span></div>" +
      '<button class="mini-btn" data-st-deck="path:' + esc(p.id) + '">' + t_("All cards of this path") + (member() ? "" : " · " + t_("members")) + "</button></div>" +
      '<ul class="fc-decks">' + p.lessons.filter((l) => l.cards.length).map((l) => '<li><button data-st-deck="lesson:' + esc(l.id) + '"><span>' + esc(l.title) + "</span><small>" +
        t_("{n} cards", { n: l.cards.length }) + (lessonFree(l) ? (l.n === 0 && !member() ? " · " + t_("free") : "") : " · " + t_("members")) + "</small></button></li>").join("") + "</ul></section>").join("");
}
function startDeck(kind, id, cards, title) {
  FCPAY = null;
  if (!cards) {
    const l = kind === "lesson" ? DATA.byLesson.get(id) : null, p = kind === "path" ? DATA.byPath.get(id) : l && l.path;
    if (!p) return false;
    const lessons = l ? [l] : p.lessons;
    if (lessons.some((x) => x.cards.length && !lessonFree(x))) { FC = null; FCPAY = p.lessons[0]; return true; }
    cards = lessons.flatMap((x) => x.cards);
    title = l ? l.title : p.title + " · " + t_("All cards");
  }
  if (!cards.length) { O.toast(t_("No flashcards here yet.")); return false; }
  FC = { title, cards: cards.slice(), i: 0, flipped: false, again: [], got: 0, done: false };
  FOCUS = ".fc-card";
  return true;
}
function deckView() {
  const n = FC.cards.length;
  if (FC.done) {
    const miss = FC.again.length;
    return '<div class="fc"><div class="fc-top"><button class="mini-btn" data-fc="close">← ' + t_("Flashcards") + '</button><span class="fc-t">' + esc(FC.title) + "</span></div>" +
      '<div class="fc-end"><b>' + t_("{n} of {all}", { n: FC.got, all: n }) + "</b><span>" + (!miss ? t_("You knew every card.") : miss === 1 ? t_("One card goes to your review and comes back tomorrow.") : t_("{m} cards go to your review and come back tomorrow.", { m: miss })) + "</span></div>" +
      '<div class="row">' + (miss ? '<button class="btn-gold" data-fc="missed">' + t_("Review the ones I missed") + " · " + miss + "</button>" : "") +
      '<button class="mini-btn" data-fc="again-all">' + t_("Start again, shuffled") + '</button><button class="mini-btn" data-fc="close">' + t_("Back to Flashcards") + "</button></div></div>";
  }
  const c = FC.cards[FC.i], place = c.place && O.byId.has(c.place) ? O.byId.get(c.place) : null, f = FC.flipped;
  return '<div class="fc"><div class="fc-top"><button class="mini-btn" data-fc="close">← ' + t_("Flashcards") + '</button><span class="fc-t">' + esc(FC.title) + '</span><span class="fc-n">' + (FC.i + 1) + " / " + n + "</span></div>" +
    '<div class="qz-bar fc-bar"><i style="width:' + (100 * FC.i / n).toFixed(1) + '%"></i></div>' +
    '<div class="fc-stage"><button class="fc-card' + (f ? " flipped" : "") + '" data-fc="flip" aria-label="' + esc(f ? t_("Answer: {text}. Turn back to the question.", { text: c.b }) : t_("Question: {text}. Turn to see the answer.", { text: c.f })) + '">' +
      '<span class="fc-face fc-front" aria-hidden="true"><small>' + esc(c.lesson.title) + '</small><span class="fc-text">' + esc(c.f) + "</span><em>" + t_("Tap or press Space to turn") + "</em></span>" +
      '<span class="fc-face fc-back" aria-hidden="true"><small>' + t_("Answer") + '</small><span class="fc-text">' + esc(c.b) + "</span></span></button></div>" +
    '<div class="fc-under"><span class="sr" aria-live="polite" id="fc-live">' + (f ? esc(c.b) : "") + "</span>" +
      (place ? '<button class="fc-map" data-fc-go="' + esc(place[1]) + '"' + (f ? "" : " hidden") + ">" + t_("See it on the map") + ": " + esc(place[0]) + " ↗</button>" : "") + "</div>" +
    '<div class="fc-grade" role="group" aria-label="' + esc(t_("Did you know it?")) + '"><button class="fc-again" data-fc="again">' + t_("Again") + ' <kbd>1</kbd></button><button class="fc-got" data-fc="got">' + t_("Got it") + " <kbd>2</kbd></button></div>" +
    '<p class="note">' + t_("Space turns the card. 1 Again, 2 Got it.") + "</p></div>";
}
function flip() {
  if (!FC || FC.done) return;
  FC.flipped = !FC.flipped;
  const el = document.querySelector(".fc-card"); if (!el) return;
  const c = FC.cards[FC.i];
  el.classList.toggle("flipped", FC.flipped);
  el.setAttribute("aria-label", FC.flipped ? t_("Answer: {text}. Turn back to the question.", { text: c.b }) : t_("Question: {text}. Turn to see the answer.", { text: c.f }));
  const live = $("fc-live"); if (live) live.textContent = FC.flipped ? c.b : "";
  const m = document.querySelector(".fc-map"); if (m) m.hidden = !FC.flipped;
}
function gradeCard(ok) {
  if (!FC || FC.done) return;
  const c = FC.cards[FC.i];
  countAnswer(c.key, ok, { flash: true });
  if (ok) FC.got++; else FC.again.push(c);
  FC.i++; FC.flipped = false;
  if (FC.i >= FC.cards.length) { FC.done = true; FOCUS = ".fc-end + .row button"; } else FOCUS = ".fc-card";
  O.renderDash();
}

// ---------- mock exam
function examHub() {
  const timer = store.get("examTimer") !== "0";
  const paths = DATA.paths.filter((p) => p.lessons.some((l) => l.questions.length));
  return '<p class="lead">' + t_("Like the real thing: questions drawn at random from every lesson of a path, no feedback until the end, then your score, a breakdown by lesson and the right answers with explanations.") + "</p>" +
    '<label class="ex-timer"><input type="checkbox" id="ex-timer"' + (timer ? " checked" : "") + "><span>" + t_("Time limit: 45 minutes for 30 questions") + "</span></label>" +
    (member() ? "" : '<p class="note">' + t_("Free: a sample exam of {n} questions for each path. Members take the full exam of {m} questions, as often as they like.", { n: SAMPLE_N, m: EXAM_N }) + "</p>") +
    '<div class="ex-paths">' + paths.map((p) => {
      const nq = p.lessons.reduce((n, l) => n + l.questions.length, 0), full = Math.min(EXAM_N, nq);
      return '<div class="ex-path' + (PICK === p.id ? " pick" : "") + '"><div><b>' + esc(p.title) + "</b><span>" + esc(p.level) + " · " + t_("{n} questions in {m} lessons", { n: nq, m: p.lessons.length }) + "</span></div>" +
        (member() ? '<button class="btn-gold" data-ex-start="' + esc(p.id) + '">' + t_("Start: {n} questions", { n: full }) + "</button>"
          : '<button class="btn-gold" data-ex-start="' + esc(p.id) + '">' + t_("Free sample: {n} questions", { n: Math.min(SAMPLE_N, nq) }) + "</button>") + "</div>";
    }).join("") + "</div>";
}
let TICK = 0;
function startExam(id) {
  const p = DATA.byPath.get(id); if (!p) return;
  const all = p.lessons.flatMap((l) => l.questions.map((q) => Object.assign(lessonQ(l, q), { lesson: l.id })));
  if (!all.length) return;
  const n = Math.min(member() ? EXAM_N : SAMPLE_N, all.length);
  const qs = shuffle(all).slice(0, n);
  EX = { path: id, sample: !member(), qs, ans: qs.map(() => -1), i: 0, t0: Date.now(), limit: store.get("examTimer") !== "0" ? Math.round(n * MIN_PER_Q) * 60000 : 0, done: false, confirm: null };
  PICK = null; FOCUS = ".ex-o button";
  clearInterval(TICK); TICK = setInterval(tick, 1000);
}
function tick() {
  if (!EX || EX.done) { clearInterval(TICK); TICK = 0; return; }
  if (!EX.limit) return;
  const left = EX.t0 + EX.limit - Date.now(), el = $("ex-clock");
  if (el) { el.textContent = mmss(left); el.classList.toggle("low", left < 5 * 60000); }
  if (left <= 0) { finishExam(true); if (O.dashOpen && O.tab === "exam") O.renderDash(); else O.toast(t_("Time is up. Your mock exam is scored in My atlas.") + ' <button data-dash="exam">' + t_("See my score") + "</button>"); }
}
function finishExam(timeUp) {
  if (!EX || EX.done) return;
  EX.done = true; EX.t1 = Date.now(); EX.timeUp = !!timeUp; EX.confirm = null;
  clearInterval(TICK); TICK = 0;
  EX.qs.forEach((q, i) => countAnswer(q.key, EX.ans[i] === q.answer, { free: true }));
  FOCUS = ".ex-score";
}
const LETTER = "ABCD";
function examView() {
  const p = DATA.byPath.get(EX.path), q = EX.qs[EX.i], n = EX.qs.length, answered = EX.ans.filter((a) => a >= 0).length, last = EX.i === n - 1;
  const left = EX.limit ? EX.t0 + EX.limit - Date.now() : 0;
  const confirm = EX.confirm === "finish" ? '<div class="ex-confirm" role="alert"><span>' + (n - answered === 1 ? t_("One question has no answer yet. Finish anyway?") : t_("{n} questions have no answer yet. Finish anyway?", { n: n - answered })) + '</span><button class="btn-gold" data-ex="finish-now">' + t_("Finish and see my score") + '</button><button class="mini-btn" data-ex="stay">' + t_("Keep going") + "</button></div>"
    : EX.confirm === "quit" ? '<div class="ex-confirm" role="alert"><span>' + t_("Leave the exam? It will not be scored.") + '</span><button class="mini-btn warn" data-ex="quit-now">' + t_("Leave the exam") + '</button><button class="mini-btn" data-ex="stay">' + t_("Keep going") + "</button></div>" : "";
  return '<div class="ex"><div class="ex-top"><button class="mini-btn" data-ex="quit">← ' + t_("Leave") + '</button><span class="ex-title">' + esc(p.title) + " · " + (EX.sample ? t_("Sample exam") : t_("Mock exam")) + "</span>" +
      (EX.limit ? '<span class="ex-clock' + (left < 5 * 60000 ? " low" : "") + '" id="ex-clock" role="timer" aria-label="' + esc(t_("Time left")) + '">' + mmss(left) + "</span>" : '<span class="ex-clock off">' + t_("No time limit") + "</span>") + "</div>" +
    '<div class="qz-bar"><i style="width:' + (100 * answered / n).toFixed(1) + '%"></i></div>' + confirm +
    '<div class="ex-n">' + t_("Question {n} of {all}", { n: EX.i + 1, all: n }) + '</div><p class="qz-q ex-q" id="ex-q">' + esc(q.q) + "</p>" +
    '<div class="ex-o" role="radiogroup" aria-labelledby="ex-q">' + q.options.map((o, i) => '<button role="radio" aria-checked="' + (EX.ans[EX.i] === i) + '" data-ex-opt="' + i + '"><span class="k">' + LETTER[i] + "</span><span>" + esc(o) + "</span></button>").join("") + "</div>" +
    '<div class="ex-nav"><button class="mini-btn" data-ex="prev"' + (EX.i ? "" : " disabled") + ">← " + t_("Previous") + "</button>" +
      (last ? '<button class="btn-gold" data-ex="finish">' + t_("Finish the exam") + "</button>" : '<button class="btn-gold" data-ex="next">' + t_("Next") + " →</button>") +
      (last ? "" : '<button class="mini-btn" data-ex="finish">' + t_("Finish the exam") + "</button>") + "</div>" +
    '<nav class="ex-grid" aria-label="' + esc(t_("Go to a question")) + '">' + EX.qs.map((x, i) => '<button data-ex-to="' + i + '" class="' + (EX.ans[i] >= 0 ? "a" : "") + '"' + (i === EX.i ? ' aria-current="step"' : "") +
      ' aria-label="' + esc(t_("Question {n}", { n: i + 1 }) + ", " + (EX.ans[i] >= 0 ? t_("answered") : t_("no answer yet"))) + '">' + (i + 1) + "</button>").join("") + "</nav>" +
    '<p class="note">' + t_("Keys: 1 to 4 choose, arrows move between questions. Nothing is marked until you finish.") + "</p></div>";
}
function examResult() {
  const p = DATA.byPath.get(EX.path), n = EX.qs.length;
  const right = EX.qs.filter((q, i) => EX.ans[i] === q.answer).length, pct = Math.round(100 * right / n), pass = pct >= PASS;
  const by = new Map(); p.lessons.forEach((l) => by.set(l.id, { l, n: 0, r: 0 }));
  EX.qs.forEach((q, i) => { const b = by.get(q.lesson); if (b) { b.n++; if (EX.ans[i] === q.answer) b.r++; } });
  const wrong = EX.qs.map((q, i) => [q, EX.ans[i]]).filter(([q, a]) => a !== q.answer);
  const mins = Math.max(1, Math.round((EX.t1 - EX.t0) / 60000));
  return '<div class="ex ex-res"><div class="ex-top"><span class="ex-title">' + esc(p.title) + " · " + (EX.sample ? t_("Sample exam") : t_("Mock exam")) + "</span></div>" +
    '<div class="ex-score" tabindex="-1"><b>' + right + " / " + n + "</b><span>" + pct + " %</span></div>" +
    '<div class="ex-meter" role="img" aria-label="' + esc(t_("Score {n} percent, pass mark {m} percent", { n: pct, m: PASS })) + '"><i style="width:' + pct + '%"></i><span class="pm" style="left:' + PASS + '%"><small>' + PASS + " %</small></span></div>" +
    '<p class="lead">' + (EX.timeUp ? t_("Time ran out.") + " " : "") + (pass ? t_("Above the pass mark of {m} %.", { m: PASS }) : t_("Below the pass mark of {m} %.", { m: PASS })) + " " +
      t_("The pass mark is a guide; each course sets its own.") + " " + t_("Time: {n} min.", { n: mins }) + "</p>" +
    (EX.sample ? memberBox(t_("That was the free sample. Members take the full mock exam of {n} questions, as often as they like.", { n: EXAM_N }), "exam") : "") +
    '<div class="row"><button class="btn-gold" data-ex="again">' + t_("Take another exam") + "</button>" + (wrong.length ? '<button class="mini-btn" data-ex="review">' + t_("Quiz me on the misses") + "</button>" : "") +
      '<button class="mini-btn" data-ex="hub">' + t_("All mock exams") + "</button></div>" +
    "<section><h3>" + t_("By lesson") + '</h3><div class="ex-bl">' + [...by.values()].filter((b) => b.n).map((b) =>
      '<div class="ex-blr"><span>' + esc(b.l.title) + '</span><span class="t"><i style="width:' + (100 * b.r / b.n).toFixed(0) + '%"></i></span><span class="v">' + b.r + " / " + b.n + "</span></div>").join("") + "</div></section>" +
    (wrong.length ? "<section><h3>" + t_("What you missed") + ' · ' + wrong.length + '</h3><p class="note">' + t_("These questions are in your review now.") + '</p><ol class="ex-wrong">' + wrong.map(([q, a]) =>
      "<li><p class=\"wq\">" + esc(q.q) + "</p><p>" + (a >= 0 ? '<span class="no">' + t_("Your answer: {a}", { a: esc(q.options[a]) }) + "</span>" : '<span class="no">' + t_("No answer") + "</span>") + "<br>" +
      '<span class="ok">' + t_("Right answer: {a}", { a: esc(q.options[q.answer]) }) + "</span></p>" + (q.explain ? '<p class="note">' + esc(q.explain) + "</p>" : "") +
      (q.place && O.byId.has(q.place) ? '<button class="mini-btn" data-go="' + esc(q.place) + '">' + esc(O.byId.get(q.place)[0]) + " ↗</button>" : "") + "</li>").join("") + "</ol></section>"
      : '<p class="lead">' + t_("No misses. Well done.") + "</p>") + "</div>";
}

// ---------- links from the rest of the page: start, lesson:<id>, path:<id>, study, hub, cards, deck:<lesson|path>:<id>, exam, exam:<path id>, review
function go(spec) {
  return loadData().then(() => {
    const [a, b, c] = String(spec || "").split(":");
    let tab = "study";
    if (a === "start") { const p = DATA.paths[0], l = p && p.lessons[0]; if (l) { VIEW = { path: p.id, lesson: l.id }; markLast(l); } }
    else if (a === "lesson" && DATA.byLesson.has(b)) { const l = DATA.byLesson.get(b); VIEW = { path: l.path.id, lesson: l.id }; markLast(l); }
    else if (a === "path" && DATA.byPath.has(b)) VIEW = { path: b, lesson: null };
    else if (a === "hub") VIEW = { path: null, lesson: null };
    else if (a === "cards") tab = "cards";
    else if (a === "deck") { tab = "cards"; startDeck(b, c); }
    else if (a === "exam") { tab = "exam"; if (b && (!EX || EX.done)) { EX = null; PICK = b; } }
    else if (a === "review") return begin(t_("Review"), reviewQs, Object.assign({}, VIEW));
    O.openDash(tab);
  }).catch(() => O.openDash("study"));
}

// ---------- events
document.addEventListener("click", (e) => {
  if (!e.target.closest("#dashBody .st")) return;
  const b = e.target.closest("[data-st], [data-st-path], [data-st-lesson], [data-st-quiz], [data-st-done], [data-st-drill], [data-st-map], [data-st-tab], [data-st-deck], [data-fc], [data-fc-go], [data-ex], [data-ex-opt], [data-ex-to], [data-ex-start], [data-ex-go]");
  if (!b || b.disabled) return;
  const d = b.dataset;
  if (d.st === "hub") { VIEW = { path: null, lesson: null }; }
  else if (d.st === "review") { const back = Object.assign({}, VIEW); return begin(t_("Review"), reviewQs, back); }
  else if (d.stTab) { return O.openDash(d.stTab); }
  else if (d.stPath) { VIEW = { path: d.stPath, lesson: null }; }
  else if (d.stLesson) { const l = DATA.byLesson.get(d.stLesson); VIEW = { path: l.path.id, lesson: l.id }; markLast(l); }
  else if (d.stDone) { const s = ST(); if (s.done[d.stDone]) delete s.done[d.stDone]; else s.done[d.stDone] = Date.now(); save(); }
  else if (d.stQuiz) {
    const l = DATA.byLesson.get(d.stQuiz), back = Object.assign({}, VIEW);
    if (!ST().done[l.id]) { ST().done[l.id] = Date.now(); save(); }
    return begin(l.title, async () => shuffle(l.questions.map((q) => lessonQ(l, q))), back);
  }
  else if (d.stDrill || d.stMap) {
    const p = DATA.byPath.get(d.stDrill || d.stMap), back = Object.assign({}, VIEW);
    if (!p.scope.length) return;
    return begin(p.title + " · " + (d.stMap ? t_("Map quiz") : t_("Region drill")), () => drillQs(p, d.stMap ? MAP_KINDS : ALL_KINDS), back);
  }
  else if (d.stDeck) { const [k, id] = d.stDeck.split(":"); startDeck(k, id); if (O.tab !== "cards") return O.openDash("cards"); }
  else if (d.fc === "flip") return flip();
  else if (d.fc === "again") return gradeCard(false);
  else if (d.fc === "got") return gradeCard(true);
  else if (d.fc === "close") { FC = null; FCPAY = null; }
  else if (d.fc === "missed") { const t = FC.title; startDeck(null, null, FC.again, t); }
  else if (d.fc === "again-all") { startDeck(null, null, shuffle(FC.cards.slice()), FC.title); }
  else if (d.fcGo) {
    const r = O.byId.get(d.fcGo); if (!r) return;
    O.closeDash(); O.goTo(r);
    O.toast(esc(r[0]) + ' <button data-dash="cards">' + t_("Back to the cards") + "</button>", 15000);
    return;
  }
  else if (d.exGo) { EX = null; PICK = d.exGo; return O.openDash("exam"); }
  else if (d.exStart) { startExam(d.exStart); }
  else if (d.exOpt != null && EX && !EX.done) { EX.ans[EX.i] = +d.exOpt; FOCUS = '[data-ex-opt="' + d.exOpt + '"]'; }
  else if (d.exTo != null && EX) { EX.i = +d.exTo; FOCUS = ".ex-q"; }
  else if (d.ex === "next" && EX) { EX.i = Math.min(EX.qs.length - 1, EX.i + 1); FOCUS = ".ex-o button"; }
  else if (d.ex === "prev" && EX) { EX.i = Math.max(0, EX.i - 1); FOCUS = ".ex-o button"; }
  else if (d.ex === "finish" && EX) { if (EX.ans.some((a) => a < 0)) { EX.confirm = "finish"; FOCUS = ".ex-confirm .btn-gold"; } else finishExam(false); }
  else if (d.ex === "finish-now") finishExam(false);
  else if (d.ex === "stay" && EX) { EX.confirm = null; FOCUS = ".ex-o button"; }
  else if (d.ex === "quit" && EX) { EX.confirm = "quit"; FOCUS = ".ex-confirm .warn"; }
  else if (d.ex === "quit-now") { clearInterval(TICK); TICK = 0; EX = null; }
  else if (d.ex === "again" && EX) { startExam(EX.path); }
  else if (d.ex === "hub") { EX = null; }
  else if (d.ex === "review" && EX) {
    const keys = EX.qs.filter((q, i) => EX.ans[i] !== q.answer).map((q) => q.key), p = DATA.byPath.get(EX.path);
    return begin(p.title + " · " + t_("Misses"), async () => (await Promise.all(keys.map(fromKey))).filter(Boolean), Object.assign({}, VIEW));
  }
  else return;
  O.renderDash();
});
document.addEventListener("change", (e) => { if (e.target.id === "ex-timer") store.set("examTimer", e.target.checked ? "1" : "0"); });
document.addEventListener("keydown", (e) => {
  if (!O.dashOpen || e.metaKey || e.ctrlKey || e.altKey || e.target.closest("input, textarea, select")) return;
  if (O.tab === "cards" && FC && !FC.done) {
    if (e.key === " ") { if (e.target.closest("button")) return; e.preventDefault(); flip(); }
    else if (e.key === "1" || e.key === "2") { e.preventDefault(); gradeCard(e.key === "2"); }
  } else if (O.tab === "exam" && EX && !EX.done && !EX.confirm) {
    const k = e.key.toLowerCase(), i = /^[1-4]$/.test(k) ? +k - 1 : "abcd".indexOf(k);
    if (i >= 0 && i < EX.qs[EX.i].options.length && (/^[1-4]$/.test(k) || e.target === document.body)) { e.preventDefault(); EX.ans[EX.i] = i; FOCUS = '[data-ex-opt="' + i + '"]'; O.renderDash(); }
    else if (e.key === "ArrowRight" && EX.i < EX.qs.length - 1) { e.preventDefault(); EX.i++; FOCUS = ".ex-o button"; O.renderDash(); }
    else if (e.key === "ArrowLeft" && EX.i > 0) { e.preventDefault(); EX.i--; FOCUS = ".ex-o button"; O.renderDash(); }
  }
});
// after each render: focus where the reader was working
function wire() {
  if (!FOCUS) return;
  const el = document.querySelector("#dashBody " + FOCUS); FOCUS = null;
  if (el) { if (el.matches(".ex-q, .ex-score")) el.setAttribute("tabindex", "-1"); el.focus({ preventScroll: true }); el.scrollIntoView({ block: "nearest" }); }
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
.st-lessons li { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; align-items: center; }
.st-lessons li > .st-lb:only-child { grid-column: 1 / -1; }
.st-lb { width: 100%; text-align: left; display: grid; gap: 2px; padding: 12px 14px; border: 1px solid var(--line); border-radius: 10px; background: #17171b; color: inherit; font: inherit; cursor: pointer; }
.st-lb:hover { border-color: #57534a; }
.st-lb span { font-weight: 500; } .st-lb small { color: var(--muted); font-size: 12px; } .st-lb.done small { color: #8fb47a; }
.st-lc { white-space: nowrap; }
.st-lesson { max-width: 680px; } .st-lesson h4 { font: 600 15px var(--f-body); margin: 22px 0 6px; } .st-lesson p { color: #d6cdbd; line-height: 1.65; margin: 0 0 10px; }
.st-places { margin: 6px 0 4px; }
.st-key { margin: 22px 0 8px; padding: 12px 14px; border-left: 3px solid var(--gold); background: #1a1712; border-radius: 0 10px 10px 0; }
.st-key ul { margin: 6px 0 0; padding-left: 18px; } .st-key li { margin: 3px 0; color: #d6cdbd; }
.st { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.st > h3 { margin-top: 6px; }
.st-stats, .st-review { margin: 0; }
kbd { font: 500 10.5px var(--f-mono); border: 1px solid currentColor; border-radius: 4px; padding: 0 4px; opacity: .65; margin-left: 4px; }
/* ways to study */
.st-modes { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; }
.st-modes button { all: unset; box-sizing: border-box; cursor: pointer; display: grid; grid-template-columns: 22px minmax(0, 1fr); gap: 3px 12px; padding: 14px 16px; border: 1px solid #4a3f28; border-radius: 12px;
  background: linear-gradient(90deg, rgba(231,192,106,.07), rgba(231,192,106,.01)); }
.st-modes button:hover { border-color: var(--gold); }
.st-modes button:focus-visible, .st-lb:focus-visible, .ex-path .btn-gold:focus-visible, .fc-decks button:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.st-modes svg { grid-row: 1 / span 2; margin-top: 3px; color: var(--gold); }
.st-modes b { font: 600 20px/1.15 var(--f-display); }
.st-modes span { color: #b8af9f; font-size: 12.5px; }
/* flashcards: the deck list */
.fc-path { border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; display: grid; gap: 8px; }
.fc-ph { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.fc-ph b { font: 600 20px/1.2 var(--f-display); display: block; } .fc-ph span { color: var(--muted); font-size: 12px; }
.fc-decks { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 6px; }
.fc-decks button { all: unset; box-sizing: border-box; cursor: pointer; width: 100%; display: grid; gap: 1px; padding: 9px 12px; border: 1px solid var(--line); border-radius: 9px; background: #17171b; }
.fc-decks button:hover { border-color: #57534a; }
.fc-decks span { font-weight: 500; font-size: 13.5px; } .fc-decks small { color: var(--muted); font-size: 12px; }
/* flashcards: the card. Front: a label on parchment; back: the cellar side */
.fc { display: grid; gap: 14px; max-width: 640px; width: 100%; }
.fc-top { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.fc-t { flex: 1; min-width: 0; font: 600 20px/1.2 var(--f-display); }
.fc-n { font: 500 12px var(--f-mono); color: var(--muted); font-variant-numeric: tabular-nums; }
.fc-bar { margin: 0; }
.fc-stage { perspective: 1600px; }
.fc-card { all: unset; box-sizing: border-box; cursor: pointer; display: grid; width: 100%; min-height: 290px; position: relative; transform-style: preserve-3d;
  transition: transform .55s cubic-bezier(.2,.7,.2,1); border-radius: 16px; }
.fc-card.flipped { transform: rotateY(180deg); }
.fc-card:focus-visible { outline: 2px solid var(--focus); outline-offset: 4px; }
.fc-face { grid-area: 1 / 1; display: grid; align-content: center; justify-items: center; gap: 16px; padding: 30px 32px; border-radius: 16px; text-align: center;
  backface-visibility: hidden; -webkit-backface-visibility: hidden; min-width: 0; }
.fc-front { background: #ebe2cf; color: #1f1a12; box-shadow: inset 0 0 0 7px #ebe2cf, inset 0 0 0 8px #a8946a, inset 0 0 0 11px #ebe2cf, inset 0 0 0 12px #c9b88f, 0 18px 40px rgba(0,0,0,.35); }
.fc-back { transform: rotateY(180deg); background: #1b1813; color: var(--parchment); box-shadow: inset 0 0 0 1px #4a3f28, inset 0 0 0 8px #1b1813, inset 0 0 0 9px #3a3122, 0 18px 40px rgba(0,0,0,.35); }
.fc-face small { font: 500 12px var(--f-body); letter-spacing: .02em; color: #7a6c55; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fc-back small { color: var(--gold); }
.fc-front .fc-text { font: 600 29px/1.22 var(--f-display); text-wrap: balance; overflow-wrap: anywhere; }
.fc-back .fc-text { font: 500 22px/1.4 var(--f-display); text-wrap: pretty; overflow-wrap: anywhere; max-width: 46ch; }
.fc-face em { font-style: normal; font-size: 12px; color: #857761; }
.fc-under { min-height: 30px; display: flex; justify-content: center; }
.fc-map { all: unset; cursor: pointer; font-size: 13px; color: var(--gold); padding: 5px 10px; border-radius: 999px; border: 1px solid #4a3f28; }
.fc-map:hover, .fc-map:focus-visible { border-color: var(--gold); }
.fc-map:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.fc-grade { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.fc-grade button, .qz-grade button { all: unset; box-sizing: border-box; cursor: pointer; text-align: center; padding: 12px; border-radius: 10px; font-weight: 600; font-size: 14px; }
button.fc-again { border: 1px solid #7a4236; background: #2a1815; color: #f0c4b8; }
button.fc-got { border: 1px solid #5a7a47; background: #182212; color: #cfe6bd; }
button.fc-again:hover { background: #351d19; } button.fc-got:hover { background: #1f2c17; }
.fc-grade button:focus-visible, .qz-grade button:focus-visible, .qz-reveal:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.fc-end { display: grid; gap: 4px; padding: 6px 0; } .fc-end b { font: 600 46px/1 var(--f-display); color: var(--gold); } .fc-end span { color: #c9c0b1; }
@media (prefers-reduced-motion: reduce) { .fc-card { transition: none; } }
@media (max-width: 760px) { .fc-card { min-height: 240px; } .fc-face { padding: 24px 20px; } .fc-front .fc-text { font-size: 25px; } .fc-back .fc-text { font-size: 19px; } }
/* flashcards in the review over the map */
.qz-kind { margin: 0 0 4px; }
button.qz-reveal { all: unset; box-sizing: border-box; cursor: pointer; text-align: center; padding: 11px 12px; border-radius: 10px; border: 1px solid #6b5a33; background: #221d12; color: var(--gold); font-weight: 600; }
.qz-back { margin: 0 0 10px; padding: 12px 14px; border-radius: 10px; background: #1b1813; border: 1px solid #3a3122; font: 500 18px/1.4 var(--f-display); color: var(--parchment); }
.qz-grade { grid-template-columns: 1fr 1fr; }
/* mock exam */
.ex-timer { display: flex; gap: 8px; align-items: center; font-size: 13.5px; color: #c9c0b1; cursor: pointer; }
.ex-timer input { accent-color: var(--gold); width: 16px; height: 16px; margin: 0; }
.ex-paths { display: grid; gap: 8px; }
.ex-path { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding: 12px 14px; border: 1px solid var(--line); border-radius: 12px; }
.ex-path.pick { border-color: var(--gold); }
.ex-path b { font: 600 20px/1.2 var(--f-display); display: block; } .ex-path span { color: var(--muted); font-size: 12px; }
.ex { display: grid; gap: 14px; max-width: 720px; }
.ex-top { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.ex-title { flex: 1; min-width: 0; font: 600 20px/1.2 var(--f-display); }
.ex-clock { font: 500 15px var(--f-mono); padding: 4px 11px; border: 1px solid var(--line); border-radius: 999px; font-variant-numeric: tabular-nums; }
.ex-clock.off { font: 400 12px var(--f-body); color: var(--muted); }
.ex-clock.low { color: #f0b4a4; border-color: #7a4236; }
.ex .qz-bar { margin: 0; }
.ex-n { font: 500 12px var(--f-mono); color: var(--muted); }
.ex-q { margin: 0; outline: none; }
.ex-o { display: grid; gap: 8px; }
.ex-o button { all: unset; box-sizing: border-box; cursor: pointer; display: grid; grid-template-columns: 26px minmax(0, 1fr); gap: 10px; align-items: start; padding: 11px 14px;
  border: 1px solid var(--line); border-radius: 10px; background: #17171b; }
.ex-o button:hover { border-color: #57534a; }
.ex-o button:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.ex-o .k { width: 24px; height: 24px; border-radius: 50%; border: 1px solid #4a463f; display: grid; place-items: center; font: 600 12px var(--f-mono); color: var(--muted); }
.ex-o button[aria-checked="true"] { border-color: var(--gold); background: #221d12; }
.ex-o button[aria-checked="true"] .k { background: var(--gold); border-color: var(--gold); color: #17130b; }
.ex-nav { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.ex-grid { display: flex; flex-wrap: wrap; gap: 4px; }
.ex-grid button { all: unset; box-sizing: border-box; cursor: pointer; width: 30px; height: 30px; display: grid; place-items: center; border: 1px solid var(--line); border-radius: 7px; font: 500 11px var(--f-mono); color: var(--muted); }
.ex-grid button.a { background: #2a261d; color: var(--parchment); border-color: #4a3f28; }
.ex-grid button[aria-current] { box-shadow: 0 0 0 2px var(--gold); }
.ex-grid button:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.ex-confirm { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 12px 14px; border: 1px solid #5a4a2a; border-radius: 10px; background: #1c1810; }
.ex-confirm span { flex: 1 1 220px; }
.ex-score { display: flex; align-items: baseline; gap: 14px; outline: none; }
.ex-score b { font: 600 56px/1 var(--f-display); color: var(--gold); font-variant-numeric: tabular-nums; }
.ex-score span { font: 500 22px var(--f-mono); color: var(--parchment); }
.ex-meter { position: relative; height: 10px; border-radius: 5px; background: #24242a; max-width: 520px; margin: 4px 0 18px; }
.ex-meter i { display: block; height: 100%; border-radius: 5px; background: var(--gold); }
.ex-meter .pm { position: absolute; top: -5px; bottom: -5px; width: 2px; margin-left: -1px; background: var(--parchment); }
.ex-meter .pm small { position: absolute; top: 22px; left: 50%; transform: translateX(-50%); font: 500 11px var(--f-mono); color: var(--muted); white-space: nowrap; }
.ex-res section { display: grid; gap: 8px; }
.ex-bl { display: grid; gap: 6px; }
.ex-blr { display: grid; grid-template-columns: minmax(0, 1fr) minmax(80px, 180px) 52px; gap: 10px; align-items: center; font-size: 13px; }
.ex-blr span:first-child { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ex-blr .t { height: 8px; background: #24242a; border-radius: 4px; overflow: hidden; } .ex-blr .t i { display: block; height: 100%; background: var(--gold); }
.ex-blr .v { font: 500 12px var(--f-mono); color: var(--muted); text-align: right; }
.ex-wrong { margin: 0; padding-left: 22px; display: grid; gap: 14px; }
.ex-wrong li { padding-left: 4px; } .ex-wrong li::marker { color: var(--muted); font: 500 12px var(--f-mono); }
.ex-wrong p { margin: 0 0 4px; } .ex-wrong .wq { font-weight: 500; }
.ex-wrong .no { color: #e8a596; } .ex-wrong .ok { color: #a9cf92; }
.ex-res p.note { margin: 0; }
.st .st-title { font: 600 28px/1.15 var(--f-display); letter-spacing: 0; text-transform: none; color: var(--parchment); margin: 6px 0 0; }
@media (max-width: 760px) {
  .ex-score b { font-size: 46px; } .ex-blr { grid-template-columns: minmax(0, 1fr) 70px 46px; }
  .ex-top .ex-title, .fc-top .fc-t { order: 3; flex-basis: 100%; font-size: 19px; }
  .ex-clock, .fc-n { margin-left: auto; }
}
`;
document.head.appendChild(css);

window.OWA_STUDY = { render, wire, loadData, member, go,
  busy: (mode) => mode === "cards" ? !!FC : mode === "exam" ? !!EX : false };
loadData().catch(() => {});
})();
