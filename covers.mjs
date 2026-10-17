// Batch cover images (1080x1920 jpg) for reels, one browser for all.
// usage: node covers.mjs list.json outdir
// list item: {key, ids:[atlas ids], bbox:[w,s,e,n], kicker, title, sub}
import fs from "node:fs";
import path from "node:path";
import { openAtlas, idle } from "./page.mjs";

const list = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const outDir = process.argv[3];
fs.mkdirSync(outDir, { recursive: true });

const CSS = `
#ovl{position:fixed;left:0;top:0;width:1080px;height:1920px;transform:scale(.5);transform-origin:0 0;pointer-events:none;z-index:50;display:block!important;color:#f6eedd}
#ovl .cv-vig{position:absolute;inset:0;background:
  radial-gradient(ellipse 80% 40% at 50% 34%, #0b0b0d00 0%, #0b0b0d40 70%, #0b0b0dbb 100%),
  linear-gradient(#0b0b0de6 0%, #0b0b0d40 14%, #0b0b0d00 24%, #0b0b0d00 48%, #0b0b0de0 61%, #0b0b0df9 72%, #0b0b0d 100%)}
#ovl .cv-brand{position:absolute;left:0;right:0;top:300px;text-align:center;font-family:"IBM Plex Mono";font-weight:500;font-size:30px;letter-spacing:.32em;color:#e7c06a;text-shadow:0 0 14px #0b0b0d,0 0 6px #0b0b0d}
#ovl .cv-txt{position:absolute;left:60px;right:60px;top:1110px;text-align:center}
#ovl .cv-kick{font-family:"IBM Plex Mono";font-weight:500;font-size:34px;letter-spacing:.18em;text-transform:uppercase;color:#d8cbb2}
#ovl .cv-h{font-family:"Cormorant Garamond";font-weight:500;line-height:.98;margin:22px 0 0;color:#f6eedd;overflow-wrap:normal;word-break:keep-all;hyphens:none}
#ovl .cv-rule{height:3px;width:150px;background:#e7c06a;margin:32px auto 0}
#ovl .cv-sub{font-family:"Cormorant Garamond";font-style:italic;font-size:62px;margin:26px 0 0;color:#efc96f}
`;

const { browser, page } = await openAtlas({ hash: "", css: CSS, globe: false });
for (const it of list) {
  const out = path.join(outDir, it.key + ".jpg");
  if (fs.existsSync(out)) continue;
  // reload on the first place (gives the atlas highlight), then frame all of them in the upper part
  await page.goto("http://atlas.local/index.html?c=" + it.key + "#" + it.ids[0], { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__map && window.__map.getStyle() && window.__map.getStyle().layers.length > 20, { timeout: 120000 });
  await page.waitForFunction(() => !!window.__map.getLayer("winery-labels"), { timeout: 60000 }).catch(() => {});
  await page.addStyleTag({ content: `body > *:not(#map):not(#ovl){display:none!important} #map{position:fixed!important;inset:0!important}
    .maplibregl-ctrl,.maplibregl-control-container{display:none!important}` + CSS });
  await new Promise((r) => setTimeout(r, 1500));
  await page.evaluate((b) => {
    const m = window.__map; m.stop(); m.resize();
    // clean background: no map labels, no winery dots (the title says it all)
    for (const L of m.getStyle().layers) if (L.type === "symbol" || /winer|poi/i.test(L.id)) m.setLayoutProperty(L.id, "visibility", "none");
    m.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: { top: 190, bottom: 430, left: 50, right: 50 }, maxZoom: 15.5, duration: 0 });
  }, it.bbox);
  await idle(page, 90000);
  // the app adds some label layers late: hide again, then wait for the repaint
  await page.evaluate(() => { const m = window.__map;
    for (const L of m.getStyle().layers) if (L.type === "symbol" || /winer|poi/i.test(L.id)) m.setLayoutProperty(L.id, "visibility", "none"); });
  await idle(page, 30000);
  await page.evaluate((it) => {
    document.getElementById("ovl")?.remove();
    const o = document.createElement("div"); o.id = "ovl";
    o.innerHTML = `<div class="cv-vig"></div><div class="cv-brand">OPEN WINE ATLAS</div>
      <div class="cv-txt"><div class="cv-kick">${it.kicker}</div><div class="cv-h">${it.title.split("<br>").map((l) => l.split(" ").map((w) => w.includes("-") ? `<span style="white-space:nowrap">${w}</span>` : w).join(" ")).join("<br>")}</div><div class="cv-rule"></div><div class="cv-sub">${it.sub}</div></div>`;
    document.body.appendChild(o);
    // largest size up to 156px where the title fits in 3 lines without breaking a word
    const h = o.querySelector(".cv-h");
    for (let s = 156; s >= 70; s -= 4) {
      h.style.fontSize = s + "px";
      const lines = Math.round(h.scrollHeight / (s * 0.98));
      if (h.scrollWidth <= h.clientWidth + 1 && lines <= (s > 120 ? 2 : 3)) break;
    }
  }, it);
  await page.evaluate(() => document.fonts.ready);
  await idle(page, 20000);
  await page.screenshot({ path: out, type: "jpeg", quality: 92 });
  console.log("ok", it.key);
}
await browser.close();
