// Deep dive, pass 2: the text and data layer, as transparent PNG frames at 30 fps (1080x1920).
// usage: node deep_ovl.mjs spec.json outdir
// Segment kinds: title, chips, card (kicker, n, u, c, chart, src, note), note, outro. Charts: months, range, compare, shares.
// Text stays out of the TikTok / Instagram / Shorts UI: top 250 px, bottom 470 px, right 150 px.
import fs from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";

const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = path.resolve(process.argv[3]);
fs.mkdirSync(out, { recursive: true });
const FPS = 30, DUR = spec.duration, N = Math.round(FPS * DUR);
const FONTS = "/home/claude/open-wine-atlas/api/fonts";

const CSS = `
@font-face{font-family:"CG";src:url(file://${FONTS}/CormorantGaramond-Medium.ttf)}
@font-face{font-family:"CG";font-style:italic;src:url(file://${FONTS}/CormorantGaramond-MediumItalic.ttf)}
@font-face{font-family:"Plex";src:url(file://${FONTS}/IBMPlexSans-Regular.ttf)}
@font-face{font-family:"Mono";src:url(file://${FONTS}/IBMPlexMono-Regular.ttf)}
@font-face{font-family:"MonoM";src:url(file://${FONTS}/IBMPlexMono-Medium.ttf)}
html,body{margin:0;background:transparent;width:1080px;height:1920px;overflow:hidden}
#o{position:absolute;inset:0;font-family:"Plex";color:#efe6d4}
.seg{position:absolute;inset:0;opacity:0}
.shade-t{position:absolute;left:0;right:0;top:0;height:760px;background:linear-gradient(#0b0b0df2 0%,#0b0b0dc8 50%,#0b0b0d00 100%)}
.shade-b{position:absolute;left:0;right:0;bottom:0;height:1320px;background:linear-gradient(#0b0b0d00 0%,#0b0b0dc8 20%,#0b0b0df0 38%,#0b0b0dfa 100%)}
.shade-c{position:absolute;left:0;right:0;top:0;height:470px;background:linear-gradient(#0b0b0de8 0%,#0b0b0db0 55%,#0b0b0d00 100%)}
.kick{font-family:"MonoM";font-size:31px;letter-spacing:.2em;text-transform:uppercase;color:#d8cbb2}
.title{position:absolute;left:80px;right:150px;top:262px}
.title h1{font-family:"CG";font-weight:500;font-size:150px;line-height:.96;margin:20px 0 0;color:#f6eedd}
.title p{font-family:"CG";font-style:italic;font-size:58px;line-height:1.12;margin:26px 0 0;color:#e2d6bf}
.rule{height:3px;width:140px;background:#e7c06a;margin-top:30px}
.chips{position:absolute;left:80px;right:150px;top:262px;display:flex;flex-wrap:wrap;gap:12px 14px}
.chip{font-family:"MonoM";font-size:24px;letter-spacing:.14em;text-transform:uppercase;padding:9px 16px 8px;border-radius:30px;border:1.5px solid #ffffff2e;color:#b9b0a1;background:#0b0b0d99}
.chip.on{color:#0b0b0d;background:#efc96f;border-color:#efc96f}
.chip.done{color:#e7d8b6;border-color:#e7c06a66}
.card{position:absolute;left:80px;right:160px;bottom:470px}
.card .n{font-family:"CG";font-weight:500;font-size:150px;line-height:1;color:#efc96f}
.card .u{font-family:"CG";font-size:66px;color:#efc96f;margin-left:12px}
.card .c{font-size:44px;line-height:1.28;margin-top:16px;color:#f3ead8}
.card .k{margin-bottom:14px}
.card .src{font-family:"Mono";font-size:24px;color:#a59d8e;letter-spacing:.04em;margin-top:26px;line-height:1.35}
.card .nt{font-family:"CG";font-size:52px;line-height:1.18;color:#f6eedd;margin-top:22px}
.card .nt i{color:#efc96f;font-style:normal}
.chart{margin-top:30px}
.note{position:absolute;left:80px;right:170px;bottom:470px;font-family:"CG";font-size:64px;line-height:1.2;color:#f6eedd}
.note i{color:#efc96f;font-style:normal}
.note .src{font-family:"Mono";font-size:24px;color:#a59d8e;margin-top:26px}
.outro{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0b0b0d;padding:0 120px 200px;text-align:center}
.outro h2{font-family:"CG";font-weight:500;font-size:120px;margin:26px 0 0;color:#f6eedd}
.outro .url{font-family:"MonoM";font-size:46px;letter-spacing:.06em;color:#efc96f;margin-top:38px}
.outro .small{font-size:34px;color:#b9b0a1;margin-top:30px;line-height:1.35}
.outro .next{font-family:"CG";font-style:italic;font-size:54px;color:#e2d6bf;margin-top:54px}
.outro .srcs{font-family:"Mono";font-size:22px;color:#8f877a;margin-top:60px;line-height:1.5;max-width:820px}
svg text{font-family:"Mono"}
`;

const esc = (s) => String(s ?? "");
function chartHTML(ch) {
  if (!ch) return "";
  const W = 840;
  if (ch.type === "months") {
    // monthly bars: series a (gold, filled), optional series b (outlined, for comparison)
    const H = 300, B = 44, top = 34, max = ch.max || Math.max(...ch.a, ...(ch.b || [0])) * 1.08;
    const slot = W / 12, bw = ch.b ? slot * 0.36 : slot * 0.6;
    let s = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`;
    for (const hl of ch.bands || []) {
      const x0 = hl.from * slot, x1 = (hl.to + 1) * slot;
      s += `<rect x="${x0}" y="${top - 30}" width="${x1 - x0}" height="${H - B - top + 30}" fill="#7fb0d61c" stroke="#7fb0d655" stroke-dasharray="4 5" rx="6"/>`;
      s += `<text x="${(x0 + x1) / 2}" y="${top - 6}" text-anchor="middle" font-size="21" fill="#a9cbe6" letter-spacing="1.5">${hl.label}</text>`;
    }
    "JFMAMJJASOND".split("").forEach((m, i) => {
      const cx = i * slot + slot / 2;
      if (ch.b) {
        s += `<rect class="bar" data-v="${ch.b[i]}" data-max="${max}" data-h="${H - B - top}" data-base="${H - B}" x="${cx + 2}" y="${H - B}" width="${bw}" height="0" fill="none" stroke="#c9c1b2" stroke-width="2" rx="3"/>`;
        s += `<rect class="bar" data-v="${ch.a[i]}" data-max="${max}" data-h="${H - B - top}" data-base="${H - B}" x="${cx - bw - 2}" y="${H - B}" width="${bw}" height="0" fill="${(ch.hot || []).includes(i) ? "#f4d27f" : "#d9ad57"}" rx="3"/>`;
      } else {
        s += `<rect class="bar" data-v="${ch.a[i]}" data-max="${max}" data-h="${H - B - top}" data-base="${H - B}" x="${cx - bw / 2}" y="${H - B}" width="${bw}" height="0" fill="${(ch.hot || []).includes(i) ? "#f4d27f" : "#d9ad57"}" rx="3"/>`;
      }
      s += `<text x="${cx}" y="${H - 12}" text-anchor="middle" font-size="24" fill="#b9b0a1">${m}</text>`;
    });
    for (const lb of ch.labels || []) {
      const cx = lb.m * slot + slot / 2 - (ch.b ? bw / 2 + 2 : 0);
      const y = H - B - (lb.v / max) * (H - B - top) - 12;
      s += `<text class="lbl" x="${cx}" y="${y}" text-anchor="middle" font-size="24" fill="#f6e3b4" opacity="0">${lb.text}</text>`;
    }
    s += `<line x1="0" x2="${W}" y1="${H - B}" y2="${H - B}" stroke="#ffffff40" stroke-width="1.5"/></svg>`;
    if (ch.legend) s += `<div style="font-family:Mono;font-size:23px;color:#b9b0a1;margin-top:10px;letter-spacing:.04em">${ch.legend}</div>`;
    return `<div class="chart">${s}</div>`;
  }
  if (ch.type === "range") {
    // monthly min to max bars (temperature), one month highlighted
    const H = 300, B = 44, top = 30, lo = ch.lo, hi = ch.hi, slot = W / 12, bw = slot * 0.5;
    const y = (v) => H - B - (v - lo) / (hi - lo) * (H - B - top);
    let s = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`;
    for (const g of ch.grid || []) s += `<line x1="0" x2="${W}" y1="${y(g)}" y2="${y(g)}" stroke="#ffffff1c" stroke-width="1"/><text x="${W}" y="${y(g) - 6}" text-anchor="end" font-size="20" fill="#8f877a">${g}°</text>`;
    "JFMAMJJASOND".split("").forEach((m, i) => {
      const cx = i * slot + slot / 2, on = i === ch.hl;
      s += `<rect class="rng" data-lo="${y(ch.min[i])}" data-hi="${y(ch.max[i])}" x="${cx - bw / 2}" y="${y(ch.min[i])}" width="${bw}" height="0" fill="${on ? "#f4d27f" : "#b8874a"}" rx="${bw / 2}"/>`;
      s += `<text x="${cx}" y="${H - 12}" text-anchor="middle" font-size="24" fill="${on ? "#f4d27f" : "#b9b0a1"}">${m}</text>`;
    });
    const cx = ch.hl * slot + slot / 2;
    if (ch.lblPos === "tb") {
      // labels above and below the highlighted bar, so they never sit on the neighbouring months
      s += `<text class="lbl" x="${cx}" y="${y(ch.max[ch.hl]) - 10}" text-anchor="middle" font-size="24" fill="#f6e3b4" opacity="0">${ch.max[ch.hl].toFixed(1)}°</text>`;
      s += `<text class="lbl" x="${cx}" y="${y(ch.min[ch.hl]) + 28}" text-anchor="middle" font-size="24" fill="#f6e3b4" opacity="0">${ch.min[ch.hl].toFixed(1)}°</text>`;
    } else {
    s += `<text class="lbl" x="${cx + bw / 2 + 10}" y="${y(ch.max[ch.hl]) + 8}" font-size="24" fill="#f6e3b4" opacity="0">${ch.max[ch.hl].toFixed(1)}°</text>`;
    s += `<text class="lbl" x="${cx + bw / 2 + 10}" y="${y(ch.min[ch.hl]) + 8}" font-size="24" fill="#f6e3b4" opacity="0">${ch.min[ch.hl].toFixed(1)}°</text>`;
    }
    s += `</svg>`;
    if (ch.legend) s += `<div style="font-family:Mono;font-size:23px;color:#b9b0a1;margin-top:10px;letter-spacing:.04em">${ch.legend}</div>`;
    return `<div class="chart">${s}</div>`;
  }
  if (ch.type === "compare") {
    const max = Math.max(...ch.rows.map((r) => r.v)) * (ch.headroom || 1.05);
    return `<div class="chart">` + ch.rows.map((r, i) => `<div style="margin:0 0 22px">
      <div style="display:flex;justify-content:space-between;font-family:Mono;font-size:27px;color:${i ? "#c9c1b2" : "#f6e3b4"};margin-bottom:9px"><span>${r.label}</span><span class="cnt" data-v="${r.v}" data-d="${r.d || 0}">0</span></div>
      <div style="height:30px;border-radius:15px;background:#ffffff14;overflow:hidden"><div class="hbar" data-w="${(r.v / max * 100).toFixed(2)}" style="height:100%;width:0;border-radius:15px;background:${i ? "#8c857a" : "#e2b45f"}"></div></div></div>`).join("") + `</div>`;
  }
  if (ch.type === "shares") {
    const cols = ["#f0c766", "#c98a4a", "#9b6a4f", "#b7a27c", "#d8cfb8", "#5d5850"];
    let bar = `<div style="display:flex;height:44px;border-radius:10px;overflow:hidden;gap:3px">`;
    ch.rows.forEach((r, i) => { bar += `<div class="seg2" data-w="${r.v}" style="width:0;background:${cols[i % cols.length]}"></div>`; });
    bar += `</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:12px 30px;margin-top:22px">`;
    ch.rows.forEach((r, i) => { bar += `<div class="leg" style="opacity:0;display:flex;align-items:center;gap:14px;font-size:30px;color:#efe6d4"><i style="display:inline-block;width:22px;height:22px;border-radius:5px;background:${cols[i % cols.length]}"></i><span style="flex:1">${r.label}</span><b style="font-family:Mono;font-weight:400;color:#f6e3b4">${r.v}%</b></div>`; });
    return `<div class="chart">${bar}</div></div>`;
  }
  return "";
}

function segHTML(s) {
  if (s.kind === "title") return `<div class="shade-t"></div><div class="title"><div class="kick">${s.kicker}</div><h1>${s.title}</h1><div class="rule"></div><p>${s.sub || ""}</p></div>`;
  if (s.kind === "chips") return `<div class="shade-c"></div><div class="chips">` + s.items.map((x, i) => `<span class="chip" data-i="${i}">${x}</span>`).join("") + `</div>`;
  if (s.kind === "card") return `<div class="shade-b"></div><div class="card"><div class="kick k">${esc(s.kicker)}</div>` +
    (s.n != null ? `<div><span class="n${s.count ? " cnt" : ""}" ${s.count ? `data-v="${s.count.v}" data-d="${s.count.d || 0}" data-pre="${s.count.pre || ""}"` : ""}>${s.n}</span><span class="u">${s.u || ""}</span></div>` : "") +
    (s.c ? `<div class="c">${s.c}</div>` : "") + (s.nt ? `<div class="nt">${s.nt}</div>` : "") + chartHTML(s.chart) + (s.src ? `<div class="src">${s.src}</div>` : "") + `</div>`;
  if (s.kind === "note") return `<div class="shade-b"></div><div class="note">${s.html}${s.src ? `<div class="src">${s.src}</div>` : ""}</div>`;
  if (s.kind === "outro") return `<div class="outro"><div class="kick">${s.kicker}</div><h2>${s.title}</h2><div class="rule" style="margin:34px auto 0"></div><div class="url">openwineatlas.com</div>` +
    `<div class="small">${s.small || ""}</div>${s.next ? `<div class="next">${s.next}</div>` : ""}${s.srcs ? `<div class="srcs">${s.srcs}</div>` : ""}</div>`;
  return "";
}

const html = `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}</style></head><body><div id="o">` +
  spec.segments.map((s, i) => `<div class="seg" data-i="${i}">${segHTML(s)}</div>`).join("") + `</div></body></html>`;
const file = path.join(out, "_overlay.html");
fs.writeFileSync(file, html);

const browser = await puppeteer.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--allow-file-access-from-files"] });
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
await page.goto("file://" + file, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);
await page.evaluate((segs) => {
  const fmt = (v, d) => v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
  const sm = (u) => { u = Math.max(0, Math.min(1, u)); return u * u * (3 - 2 * u); };
  window.__setT = (t) => {
    const sig = [];
    document.querySelectorAll(".seg").forEach((el) => {
      const s = segs[+el.dataset.i], fi = s.fadeIn ?? 0.6, fo = s.fadeOut ?? 0.6;
      let a = 0;
      if (t >= s.t0 && t <= s.t1) a = Math.min(1, (t - s.t0) / fi, s.t1 >= 999 ? 1 : (s.t1 - t) / fo);
      a = Math.max(0, a);
      el.style.opacity = a.toFixed(3);
      el.style.visibility = a > 0 ? "visible" : "hidden";
      const rise = (1 - sm((t - s.t0) / (fi * 1.6))) * 26;
      el.style.transform = s.kind === "outro" || s.kind === "chips" ? "" : `translateY(${rise.toFixed(1)}px)`;
      sig.push(a.toFixed(3), rise.toFixed(1));
      if (a <= 0) return;
      // chart and counter progress, from 0.5 s after the segment starts
      const p = sm((t - s.t0 - (s.delay ?? 0.5)) / (s.grow ?? 1.4));
      sig.push(p.toFixed(3));
      el.querySelectorAll(".bar").forEach((b, k) => {
        const q = sm((t - s.t0 - (s.delay ?? 0.5) - k * 0.035) / (s.grow ?? 1.1));
        const h = (+b.dataset.v / +b.dataset.max) * +b.dataset.h * q;
        b.setAttribute("height", h.toFixed(1)); b.setAttribute("y", (+b.dataset.base - h).toFixed(1));
      });
      el.querySelectorAll(".rng").forEach((b, k) => {
        const q = sm((t - s.t0 - (s.delay ?? 0.5) - k * 0.04) / (s.grow ?? 1.1));
        const lo = +b.dataset.lo, hi = +b.dataset.hi, mid = (lo + hi) / 2, half = (lo - hi) / 2 * q;
        b.setAttribute("y", (mid - half).toFixed(1)); b.setAttribute("height", (2 * half).toFixed(1));
      });
      const pl = sm((t - s.t0 - (s.delay ?? 0.5) - (s.grow ?? 1.4) - 0.2) / 0.5);
      sig.push(pl.toFixed(3), t - s.t0 < 3.2 ? t.toFixed(3) : "");
      el.querySelectorAll(".lbl,.leg").forEach((x) => { x.setAttribute("opacity", pl.toFixed(3)); x.style.opacity = pl.toFixed(3); });
      el.querySelectorAll(".hbar").forEach((x) => { x.style.width = (+x.dataset.w * p).toFixed(2) + "%"; });
      el.querySelectorAll(".seg2").forEach((x) => { x.style.width = (+x.dataset.w * p).toFixed(2) + "%"; });
      el.querySelectorAll(".cnt").forEach((x) => { x.textContent = (x.dataset.pre || "") + fmt(+x.dataset.v * p, +x.dataset.d); });
      if (s.kind === "chips") {
        el.querySelectorAll(".chip").forEach((c, i) => {
          const [a0, a1] = s.spans[i];
          c.className = "chip" + (t >= a0 && t < a1 ? " on" : t >= a1 ? " done" : "");
          sig.push(c.className);
        });
      }
    });
    return sig.join("|");
  };
}, spec.segments);

// preview: node deep_ovl.mjs spec out --at 3,10,25 renders only those moments, on a dark grey plate
const atArg = process.argv.indexOf("--at");
if (atArg > 0) {
  for (const tt of process.argv[atArg + 1].split(",").map(Number)) {
    await page.evaluate((t) => window.__setT(t), tt);
    await page.evaluate(() => { document.body.style.background = "#3a3d3a"; });
    await page.screenshot({ path: path.join(out, "at_" + tt + ".jpg"), type: "jpeg", quality: 85 });
  }
  await browser.close();
  process.exit(0);
}
let prev = null, prevFile = null, made = 0;
const T0 = Date.now();
for (let f = 0; f < N; f++) {
  const fileOut = path.join(out, String(f).padStart(5, "0") + ".png");
  const sig = await page.evaluate((t) => window.__setT(t), f / FPS);
  if (sig === prev && prevFile) { fs.copyFileSync(prevFile, fileOut); continue; }
  await page.screenshot({ path: fileOut, type: "png", omitBackground: true });
  prev = sig; prevFile = fileOut; made++;
}
console.log("overlay", N, "frames,", made, "rendered,", ((Date.now() - T0) / 1000).toFixed(0), "s");
await browser.close();
