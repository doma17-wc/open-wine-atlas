// Cover for a deep dive (1080x1920 jpg): a map frame behind the title, the title in the middle third so it reads in the 3:4 profile grid.
// usage: node deep_cover.mjs background.jpg out.jpg '{"kicker":"Deep dive · Japan","title":"Yamanashi","sub":"Japan's first wine GI"}'
import fs from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";

const [bg, out, json] = process.argv.slice(2);
const it = JSON.parse(json);
const F = "/home/claude/open-wine-atlas/api/fonts";
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:CG;src:url(file://${F}/CormorantGaramond-Medium.ttf)}
@font-face{font-family:CG;font-style:italic;src:url(file://${F}/CormorantGaramond-MediumItalic.ttf)}
@font-face{font-family:MonoM;src:url(file://${F}/IBMPlexMono-Medium.ttf)}
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0b0b0d}
.bg{position:absolute;inset:0;background:url(file://${path.resolve(bg)}) center/cover}
.vig{position:absolute;inset:0;background:radial-gradient(ellipse 85% 42% at 50% 50%,#0b0b0d00 0%,#0b0b0d55 70%,#0b0b0dcc 100%),
 linear-gradient(#0b0b0de0 0%,#0b0b0d30 16%,#0b0b0d10 30%,#0b0b0db0 46%,#0b0b0dd8 58%,#0b0b0d60 72%,#0b0b0de8 100%)}
.brand{position:absolute;left:0;right:0;top:300px;text-align:center;font-family:MonoM;font-size:30px;letter-spacing:.32em;color:#e7c06a}
.txt{position:absolute;left:60px;right:60px;top:760px;text-align:center}
.kick{font-family:MonoM;font-size:36px;letter-spacing:.2em;text-transform:uppercase;color:#e9dcc2}
h1{font-family:CG;font-weight:500;font-size:${it.size || 170}px;line-height:.96;margin:24px 0 0;color:#f6eedd}
.rule{height:3px;width:150px;background:#e7c06a;margin:34px auto 0}
.sub{font-family:CG;font-style:italic;font-size:64px;line-height:1.1;margin:28px 0 0;color:#efc96f}
</style></head><body><div class="bg"></div><div class="vig"></div><div class="brand">OPEN WINE ATLAS</div>
<div class="txt"><div class="kick">${it.kicker}</div><h1>${it.title}</h1><div class="rule"></div><div class="sub">${it.sub || ""}</div></div></body></html>`;
const file = path.resolve(out + ".html");
fs.writeFileSync(file, html);
const browser = await puppeteer.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", headless: true, args: ["--no-sandbox", "--allow-file-access-from-files"] });
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1920 });
await page.goto("file://" + file, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: out, type: "jpeg", quality: 92 });
await browser.close();
fs.unlinkSync(file);
console.log("cover", out);
