// Renders one reel (1080x1920 frames) from the real atlas page: globe fly-in, gold highlight, title and fact cards.
// usage: node render.mjs spec.json outdir [startFrame endFrame]
import fs from "node:fs";
import path from "node:path";
import { openAtlas, idle } from "./page.mjs";

const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = process.argv[3];
fs.mkdirSync(out, { recursive: true });
const FPS = spec.fps || 30, DUR = spec.duration || 24, N = Math.round(FPS * DUR);
const from = +(process.argv[4] || 0), to = +(process.argv[5] || N);

const OVL_CSS = `
#ovl{position:fixed;left:0;top:0;width:1080px;height:1920px;transform:scale(.5);transform-origin:0 0;pointer-events:none;z-index:50;display:block!important;font-family:"IBM Plex Sans";color:#efe6d4}
#ovl .shade-t{position:absolute;left:0;right:0;top:0;height:760px;background:linear-gradient(#0b0b0df5 0%,#0b0b0dd0 50%,#0b0b0d00 100%)}
#ovl .shade-b{position:absolute;left:0;right:0;bottom:0;height:1050px;background:linear-gradient(#0b0b0d00 0%,#0b0b0dd8 40%,#0b0b0df7 100%)}
#ovl .kick{font-family:"IBM Plex Mono";font-weight:500;font-size:32px;letter-spacing:.2em;text-transform:uppercase;color:#d8cbb2}
#ovl .title{position:absolute;left:80px;right:150px;top:255px}
#ovl .title h1{font-family:"Cormorant Garamond";font-weight:500;font-size:140px;line-height:.98;margin:20px 0 0;color:#f6eedd}
#ovl .title p{font-family:"Cormorant Garamond";font-style:italic;font-size:56px;margin:26px 0 0;color:#e2d6bf}
#ovl .rule{height:3px;width:140px;background:#e7c06a;margin-top:30px}
#ovl .fact{position:absolute;left:80px;right:170px;bottom:470px}
#ovl .fact .n{font-family:"Cormorant Garamond";font-weight:500;font-size:168px;line-height:1;color:#efc96f}
#ovl .fact .u{font-family:"Cormorant Garamond";font-size:72px;color:#efc96f;margin-left:12px}
#ovl .fact .c{font-size:50px;line-height:1.28;margin-top:22px;color:#f3ead8}
#ovl .fact .k{margin-bottom:20px}
#ovl .note{position:absolute;left:80px;right:170px;bottom:470px;font-family:"Cormorant Garamond";font-size:66px;line-height:1.2;color:#f6eedd}
#ovl .note i{color:#efc96f;font-style:normal}
#ovl .outro{position:absolute;left:0;right:0;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0b0b0d;padding-bottom:180px}
#ovl .outro h2{font-family:"Cormorant Garamond";font-weight:500;font-size:112px;margin:0;color:#f6eedd;text-align:center}
#ovl .outro .url{font-family:"IBM Plex Mono";font-weight:500;font-size:46px;letter-spacing:.06em;color:#efc96f;margin-top:38px}
#ovl .outro .small{font-size:36px;color:#b9b0a1;margin-top:30px;font-family:"IBM Plex Sans"}
#ovl .src{position:absolute;left:80px;right:150px;top:250px;font-family:"IBM Plex Mono";font-size:30px;color:#b3a993;letter-spacing:.05em;line-height:1.4;text-shadow:0 0 10px #0b0b0d,0 0 4px #0b0b0d,0 0 2px #0b0b0d}
#ovl .seg{position:absolute;inset:0;opacity:0}
`;

const { browser, page } = await openAtlas({ hash: spec.id, css: OVL_CSS, globe: true, labelScale: spec.labelScale || 1.55 });
if (from === 0) console.log("labels:", (await page.evaluate(() => window.__labelReport)).join(", "));

// overlay markup: one block per segment, faded by time
await page.evaluate((spec) => {
  const o = document.createElement("div"); o.id = "ovl";
  const segs = spec.segments.map((s, i) => {
    let inner = "";
    if (s.kind === "title") inner = `<div class="shade-t"></div><div class="title"><div class="kick">${s.kicker}</div><h1>${s.title}</h1><div class="rule"></div><p>${s.sub || ""}</p></div>`;
    if (s.kind === "fact") inner = `<div class="shade-b"></div><div class="fact"><div class="kick k">${s.kicker || ""}</div><div><span class="n">${s.n}</span><span class="u">${s.u || ""}</span></div><div class="c">${s.c}</div></div>`;
    if (s.kind === "note") inner = `<div class="shade-b"></div><div class="note">${s.html}</div>`;
    if (s.kind === "outro") inner = `<div class="outro"><div class="kick">${s.kicker}</div><h2 style="margin-top:26px">${s.title}</h2><div class="rule" style="margin:34px auto 0"></div><div class="url">openwineatlas.com</div><div class="small">${s.small || ""}</div></div>`;
    if (s.kind === "src") inner = `<div class="src">${s.text}</div>`;
    return `<div class="seg" data-i="${i}">${inner}</div>`;
  });
  o.innerHTML = segs.join("");
  document.body.appendChild(o);
  window.__segs = spec.segments;
  window.__setT = (t) => {
    o.querySelectorAll(".seg").forEach((el) => {
      const s = window.__segs[+el.dataset.i], fi = s.fadeIn ?? 0.6, fo = s.fadeOut ?? 0.6;
      let a = 0;
      if (t >= s.t0 && t <= s.t1) a = Math.min(1, (t - s.t0) / fi, s.t1 >= 999 ? 1 : (s.t1 - t) / fo);
      el.style.opacity = Math.max(0, a).toFixed(3);
      const rise = (1 - Math.min(1, Math.max(0, (t - s.t0) / (fi * 1.6)))) * 26;
      el.style.transform = s.kind === "outro" || s.kind === "src" ? "" : `translateY(${rise.toFixed(1)}px)`;
    });
  };
}, spec);

await page.evaluate(() => { const m = window.__map; m.setPadding({ top: 0, bottom: 0, left: 0, right: 0 }); m.stop(); });

// camera path: keyframes [t, lng, lat, zoom, bearing, pitch], smooth (cosine) between keyframes, zoom in log space already
const K = spec.camera;
const ease = (x) => x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
function cam(t) {
  if (t <= K[0][0]) return K[0];
  for (let i = 0; i < K.length - 1; i++) {
    const a = K[i], b = K[i + 1];
    if (t >= a[0] && t <= b[0]) {
      const u = ease((t - a[0]) / (b[0] - a[0]));
      // centre follows zoom so the place stays in view while flying in (van Wijk-like: centre moves early when zoomed out)
      const uz = u, uc = Math.min(1, u * (b[3] > a[3] + 2 ? 1.35 : 1));
      return [t, a[1] + (b[1] - a[1]) * uc, a[2] + (b[2] - a[2]) * uc, a[3] + (b[3] - a[3]) * uz, a[4] + (b[4] - a[4]) * u, a[5] + (b[5] - a[5]) * u];
    }
  }
  return K[K.length - 1];
}

// warm the tile cache at the key views
for (const k of K) {
  await page.evaluate((k) => window.__map.jumpTo({ center: [k[1], k[2]], zoom: k[3], bearing: k[4], pitch: k[5] }), k);
  await idle(page, 60000);
}

// map padding (CSS px, 540x960 page): globe sits below the title at the start, place sits above the fact cards later
const lerp = (a, b, u) => a + (b - a) * Math.max(0, Math.min(1, u));
const sm = (u) => { u = Math.max(0, Math.min(1, u)); return u * u * (3 - 2 * u); };
function pad(t) {
  const P = spec.pad || { top: 250, topEnd: [4.5, 7.5], bottom: 360, bottomStart: [7.0, 9.4] };
  return { top: lerp(P.top, 0, sm((t - P.topEnd[0]) / (P.topEnd[1] - P.topEnd[0]))),
           bottom: lerp(0, P.bottom, sm((t - P.bottomStart[0]) / (P.bottomStart[1] - P.bottomStart[0]))), left: 0, right: 0 };
}
const t0 = Date.now();
for (let f = from; f < to; f++) {
  const t = f / FPS, c = cam(t);
  await page.evaluate((c, t, p) => { window.__map.jumpTo({ center: [c[1], c[2]], zoom: c[3], bearing: c[4], pitch: c[5], padding: p }); window.__setT(t); }, c, t, pad(t));
  await idle(page, 20000);
  await page.screenshot({ path: path.join(out, String(f).padStart(5, "0") + ".jpg"), type: "jpeg", quality: 95 });
  if (f % 30 === 0) console.log("frame", f, "/", N, ((Date.now() - t0) / 1000 / (f - from + 1)).toFixed(2), "s/frame");
}
await browser.close();
