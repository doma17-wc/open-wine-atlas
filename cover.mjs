// Cover image (1080x1920 jpg) for a reel: the place on the real atlas map, title big in the middle third,
// so it still reads in the 3:4 profile grid of TikTok and Instagram.
// usage: node cover.mjs spec.json out.jpg
import fs from "node:fs";
import { openAtlas, idle } from "./page.mjs";

const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = process.argv[3];
const c = spec.cover || {};
const last = spec.camera[spec.camera.length - 1];
const view = c.view || [last[1], last[2], last[3] - 0.8, last[4], Math.min(last[5], 30)];
const title = spec.segments.find((s) => s.kind === "title");

const CSS = `
#ovl{position:fixed;left:0;top:0;width:1080px;height:1920px;transform:scale(.5);transform-origin:0 0;pointer-events:none;z-index:50;display:block!important;color:#f6eedd}
#ovl .cv-vig{position:absolute;inset:0;background:
  radial-gradient(ellipse 75% 38% at 50% 34%, #0b0b0d00 0%, #0b0b0d55 70%, #0b0b0dcc 100%),
  linear-gradient(#0b0b0de6 0%, #0b0b0d40 14%, #0b0b0d00 26%, #0b0b0d00 46%, #0b0b0dd9 60%, #0b0b0df7 72%, #0b0b0d 100%)}
#ovl .cv-brand{position:absolute;left:0;right:0;top:300px;text-align:center;font-family:"IBM Plex Mono";font-weight:500;font-size:30px;letter-spacing:.32em;color:#e7c06a;text-shadow:0 0 14px #0b0b0d,0 0 6px #0b0b0d}
#ovl .cv-txt{position:absolute;left:60px;right:60px;top:1110px;text-align:center}
#ovl .cv-kick{font-family:"IBM Plex Mono";font-weight:500;font-size:34px;letter-spacing:.2em;text-transform:uppercase;color:#d8cbb2}
#ovl h1{font-family:"Cormorant Garamond";font-weight:500;font-size:${c.size || 156}px;line-height:.95;margin:24px 0 0;color:#f6eedd}
#ovl .cv-rule{height:3px;width:150px;background:#e7c06a;margin:34px auto 0}
#ovl p{font-family:"Cormorant Garamond";font-style:italic;font-size:64px;margin:28px 0 0;color:#efc96f}
`;

const { browser, page } = await openAtlas({ hash: spec.id, css: CSS, globe: false, labelScale: spec.labelScale || 1.55 });
await page.evaluate((v) => {
  const m = window.__map; m.stop();
  m.jumpTo({ center: [v[0], v[1]], zoom: v[2], bearing: v[3], pitch: v[4], padding: { top: 150, bottom: 390, left: 0, right: 0 } });
}, view);
await idle(page, 90000);
await page.evaluate((t, c) => {
  const o = document.createElement("div"); o.id = "ovl";
  o.innerHTML = `<div class="cv-vig"></div><div class="cv-brand">OPEN WINE ATLAS</div>
    <div class="cv-txt"><div class="cv-kick">${c.kicker || t.kicker}</div><h1>${c.title || t.title}</h1><div class="cv-rule"></div><p>${c.sub || t.sub || ""}</p></div>`;
  document.body.appendChild(o);
}, title, c);
await page.evaluate(() => document.fonts.ready);
await idle(page, 30000);
await page.screenshot({ path: out, type: "jpeg", quality: 93 });
await browser.close();
console.log("cover", out);
