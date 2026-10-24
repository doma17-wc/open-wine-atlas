// Opens the real atlas page (web/index.html) in headless Chromium, everything served from disk.
import fs from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";
import { execFile } from "node:child_process";
import crypto from "node:crypto";

const CACHE = "/home/claude/rend/tilecache";
fs.mkdirSync(CACHE, { recursive: true });
// terrain tiles come through curl (it knows the proxy and its CA), cached on disk
const INFLIGHT = new Map();
function fetchTile(u) {
  const f = path.join(CACHE, crypto.createHash("md5").update(u).digest("hex"));
  if (fs.existsSync(f)) return Promise.resolve(fs.readFileSync(f));
  // one download per tile even when the page asks twice at once; a unique temp name, never a crash on rename
  if (INFLIGHT.has(f)) return INFLIGHT.get(f);
  const part = f + "." + process.pid + "." + Math.random().toString(36).slice(2) + ".part";
  const pr = new Promise((res) => execFile("curl", ["-sS", "-f", "--max-time", "40", "--retry", "2", "-o", part, u], (err) => {
    INFLIGHT.delete(f);
    if (err) { try { fs.unlinkSync(part); } catch (e) {} return res(null); }
    try { fs.renameSync(part, f); return res(fs.readFileSync(f)); }
    catch (e) { try { return res(fs.readFileSync(fs.existsSync(f) ? f : part)); } catch (e2) { return res(null); } }
  }));
  INFLIGHT.set(f, pr);
  return pr;
}

const WEBDIR = "/home/claude/open-wine-atlas/web";
const FONTDIR = "/home/claude/open-wine-atlas/api/fonts";
const NM = path.join(path.dirname(new URL(import.meta.url).pathname), "node_modules");
const ORIGIN = "http://atlas.local/";

const FONT_CSS = `
@font-face{font-family:"Cormorant Garamond";font-weight:500;src:url(${ORIGIN}__font/CormorantGaramond-Medium.ttf)}
@font-face{font-family:"Cormorant Garamond";font-weight:600;src:url(${ORIGIN}__font/CormorantGaramond-Medium.ttf)}
@font-face{font-family:"Cormorant Garamond";font-style:italic;font-weight:500;src:url(${ORIGIN}__font/CormorantGaramond-MediumItalic.ttf)}
@font-face{font-family:"IBM Plex Sans";font-weight:400;src:url(${ORIGIN}__font/IBMPlexSans-Regular.ttf)}
@font-face{font-family:"IBM Plex Sans";font-weight:500;src:url(${ORIGIN}__font/IBMPlexSans-Regular.ttf)}
@font-face{font-family:"IBM Plex Sans";font-weight:600;src:url(${ORIGIN}__font/IBMPlexSans-Regular.ttf)}
@font-face{font-family:"IBM Plex Mono";font-weight:400;src:url(${ORIGIN}__font/IBMPlexMono-Regular.ttf)}
@font-face{font-family:"IBM Plex Mono";font-weight:500;src:url(${ORIGIN}__font/IBMPlexMono-Medium.ttf)}`;

const TYPES = { ".html": "text/html", ".js": "application/javascript", ".json": "application/json", ".css": "text/css",
  ".pbf": "application/x-protobuf", ".pmtiles": "application/octet-stream", ".ttf": "font/ttf", ".txt": "text/plain" };

function serveFile(req, file) {
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) return req.respond({ status: 404, body: "" });
  const size = fs.statSync(file).size, type = TYPES[path.extname(file)] || "application/octet-stream";
  const range = req.headers()["range"];
  const base = { "Content-Type": type, "Accept-Ranges": "bytes", "Access-Control-Allow-Origin": "*" };
  if (range) {
    const m = range.match(/bytes=(\d+)-(\d*)/);
    const a = +m[1], b = m[2] ? Math.min(+m[2], size - 1) : size - 1;
    const buf = Buffer.alloc(b - a + 1); const fd = fs.openSync(file, "r"); fs.readSync(fd, buf, 0, buf.length, a); fs.closeSync(fd);
    return req.respond({ status: 206, headers: { ...base, "Content-Range": `bytes ${a}-${b}/${size}` }, body: buf });
  }
  return req.respond({ status: 200, headers: base, body: fs.readFileSync(file) });
}

export async function openAtlas({ width = 540, height = 960, scale = 2, hash = "", css = "", globe = false, labelScale = 1.55 } = {}) {
  const browser = await puppeteer.launch({
    executablePath: "/opt/pw-browsers/chromium-1243/chrome-linux64/chrome",
    headless: true,
    args: ["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-dev-shm-usage"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width, height, deviceScaleFactor: scale });
  await page.setRequestInterception(true);
  page.on("request", (req) => {
    const u = req.url();
    if (u.startsWith("data:") || u.startsWith("blob:")) return req.continue();
    if (u.includes("maplibre-gl@") && u.endsWith("maplibre-gl.js")) return serveFile(req, path.join(NM, "maplibre-gl/dist/maplibre-gl.js"));
    if (u.includes("pmtiles@") && u.endsWith("pmtiles.js")) return serveFile(req, path.join(NM, "pmtiles/dist/pmtiles.js"));
    if (u.startsWith("https://fonts.googleapis.com/css")) return req.respond({ status: 200, headers: { "Content-Type": "text/css" }, body: FONT_CSS });
    if (u.startsWith(ORIGIN + "__font/")) return serveFile(req, path.join(FONTDIR, u.slice((ORIGIN + "__font/").length)));
    if (u.startsWith(ORIGIN)) {
      let p = decodeURIComponent(new URL(u).pathname.slice(1)) || "index.html";
      return serveFile(req, path.join(WEBDIR, p));
    }
    if (u.startsWith("https://tiles.mapterhorn.com/")) {
      return fetchTile(u).then((b) => b ? req.respond({ status: 200, headers: { "Content-Type": "image/webp", "Access-Control-Allow-Origin": "*" }, body: b })
                                        : req.respond({ status: 404, body: "" }));
    }
    return req.respond({ status: 404, body: "" }); // rest of the outside world (satellite, weather) stays off
  });
  page.on("pageerror", (e) => console.error("pageerror", e.message));
  await page.evaluateOnNewDocument((globe) => {
    try { localStorage.setItem("owa.proj", globe ? "globe" : "flat"); } catch (e) {}
  }, globe);
  await page.goto(ORIGIN + "index.html" + (hash ? "#" + hash : ""), { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__map && window.__map.getStyle() && window.__map.getStyle().layers.length > 20, { timeout: 120000 });
  // let the app finish adding its layers (overview, poi)
  await page.waitForFunction(() => !!window.__map.getLayer("winery-labels"), { timeout: 120000 }).catch(() => {});
  await page.addStyleTag({ content: `body > *:not(#map):not(#ovl){display:none!important} #map{position:fixed!important;inset:0!important}
    .maplibregl-ctrl,.maplibregl-control-container{display:none!important} ${css}` });
  await page.evaluate(() => { window.__map.resize(); });
  await page.evaluate(boostLabels, labelScale);
  return { browser, page };
}

export async function idle(page, timeout = 30000) {
  await page.evaluate((timeout) => new Promise((res) => {
    const m = window.__map; const t = setTimeout(res, timeout);
    const done = () => { clearTimeout(t); res(); };
    if (m.loaded() && m.areTilesLoaded()) { m.once("idle", done); m.triggerRepaint(); } else m.once("idle", done);
  }), timeout);
}

// Runs in the page: makes map labels readable on a phone. Sizes up every text label, lightens its colour,
// thickens the halo, and drops the tiny winery/POI labels that only add clutter at video size.
function boostLabels(k) {
  const m = window.__map;
  const lighten = (c) => {
    if (typeof c !== "string") return c;
    let r, g, b, a = 1, mm;
    if ((mm = c.match(/^#([0-9a-f]{6})$/i))) { r = parseInt(mm[1].slice(0, 2), 16); g = parseInt(mm[1].slice(2, 4), 16); b = parseInt(mm[1].slice(4, 6), 16); }
    else if ((mm = c.match(/^#([0-9a-f]{3})$/i))) { [r, g, b] = mm[1].split("").map((h) => parseInt(h + h, 16)); }
    else if ((mm = c.match(/^rgba?\(([^)]+)\)$/))) { const p = mm[1].split(",").map(Number); [r, g, b] = p; if (p.length > 3) a = p[3]; }
    else return c;
    const t = 0.55; // move 55% of the way towards warm ivory
    r = Math.round(r + (241 - r) * t); g = Math.round(g + (232 - g) * t); b = Math.round(b + (214 - b) * t);
    a = Math.min(1, a + (1 - a) * 0.6);
    return `rgba(${r},${g},${b},${a.toFixed(2)})`;
  };
  const deepColor = (e) => Array.isArray(e) ? e.map(deepColor) : lighten(e);
  const scaleSize = (e) => {
    if (typeof e === "number") return +(e * k).toFixed(2);
    if (Array.isArray(e) && (e[0] === "interpolate" || e[0] === "interpolate-hcl" || e[0] === "interpolate-lab")) {
      const out = e.slice(0, 3);
      for (let i = 3; i < e.length; i += 2) out.push(e[i], scaleSize(e[i + 1]));
      return out;
    }
    if (Array.isArray(e) && e[0] === "step") {
      const out = e.slice(0, 2); out.push(scaleSize(e[2]));
      for (let i = 3; i < e.length; i += 2) out.push(e[i], scaleSize(e[i + 1]));
      return out;
    }
    if (Array.isArray(e)) return ["*", e, k];
    return e;
  };
  const hide = /winer|poi|producer|estate/i;
  const report = [];
  for (const L of m.getStyle().layers) {
    if (L.type !== "symbol") continue;
    if (hide.test(L.id)) { m.setLayoutProperty(L.id, "visibility", "none"); report.push("hide " + L.id); continue; }
    const ts = m.getLayoutProperty(L.id, "text-size");
    if (ts === undefined && !m.getLayoutProperty(L.id, "text-field")) continue;
    try { m.setLayoutProperty(L.id, "text-size", scaleSize(ts === undefined ? 16 : ts)); } catch (err) { report.push("size-fail " + L.id); }
    try { const tc = m.getPaintProperty(L.id, "text-color"); if (tc !== undefined) m.setPaintProperty(L.id, "text-color", deepColor(tc)); } catch (err) { report.push("color-fail " + L.id); }
    try { const hw = m.getPaintProperty(L.id, "text-halo-width"); m.setPaintProperty(L.id, "text-halo-width", typeof hw === "number" ? Math.max(1.6, hw * 1.5) : 1.6);
          m.setPaintProperty(L.id, "text-halo-color", "rgba(10,10,12,0.9)"); } catch (err) {}
    try { m.setLayoutProperty(L.id, "text-padding", 6); } catch (err) {}
    report.push("boost " + L.id);
  }
  window.__labelReport = report;
}
