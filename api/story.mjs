// Share image of one atlas place: /api/story?id=fr-inao-a166 (or ?q=Corton-Charlemagne)
// Renders a PNG with the place's real outline, open orthophotos where their licence allows reuse,
// and the key facts from the details file. Formats: story (1080x1920, default), post (1080x1350), square (1080x1080).
// Everything is read from web/data inside the function bundle, so it works the same on previews and production.
import fs from "node:fs";
import path from "node:path";
import { PMTiles } from "pmtiles";
import { VectorTile } from "@mapbox/vector-tile";
import Pbf from "pbf";
import { Resvg } from "@resvg/resvg-js";

const ROOT = process.cwd();
const DATA = path.join(ROOT, "web", "data");
const FONTS = path.join(ROOT, "api", "fonts");

const C = { night: "#0b0b0d", land: "#151518", line: "#2a2a31", parchment: "#e6dccb", muted: "#8d877c",
  gold: "#e7c06a", copper: "#cf8f5f", slate: "#9db0c0", vine: "#7f9b6f" };
const TOP = new Set(["grand_cru", "docg", "doca", "pago"]);
const FORMATS = {
  story: { w: 1080, h: 1920, mapH: 1150, fit: [80, 440, 1000, 960], safeTop: 250 },
  post: { w: 1080, h: 1350, mapH: 860, fit: [80, 250, 1000, 700], safeTop: 64 },
  square: { w: 1080, h: 1080, mapH: 1080, fit: [90, 340, 990, 790], safeTop: 64 },
};

// ---------- data, read once per warm function
const cache = new Map();
const once = (k, fn) => (cache.has(k) ? cache.get(k) : (cache.set(k, fn()), cache.get(k)));
const readJSON = (f) => once("json:" + f, () => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8")));

class FileSource {
  constructor(file) { this.file = file; this.fd = fs.openSync(file, "r"); }
  getKey() { return this.file; }
  async getBytes(offset, length) {
    const b = Buffer.alloc(length);
    fs.readSync(this.fd, b, 0, length, offset);
    return { data: b.buffer.slice(b.byteOffset, b.byteOffset + length) };
  }
}
const pmtiles = (f) => once("pm:" + f, () => new PMTiles(new FileSource(path.join(DATA, f))));

function findPlace(id, q) {
  const rows = readJSON("search.json");
  if (id) return rows.find((r) => r[1] === id) || null;
  if (!q) return null;
  const k = q.trim().toLowerCase();
  // exact name first, preferring the most specific level, then a prefix match
  const exact = rows.filter((r) => r[0].toLowerCase() === k);
  const order = ["vineyard", "subzone", "appellation", "region", "vineyard_area"];
  exact.sort((a, b) => order.indexOf(a[3]) - order.indexOf(b[3]));
  return exact[0] || rows.find((r) => r[0].toLowerCase().startsWith(k)) || null;
}

// ---------- web mercator
const TILE = 256;
const wx = (lon, z) => ((lon + 180) / 360) * TILE * 2 ** z;
const wy = (lat, z) => {
  const s = Math.sin((lat * Math.PI) / 180);
  return (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * TILE * 2 ** z;
};

// ---------- which tiles hold the outline
function vectorSourceFor(rec) {
  const [, , cc, level, , , bbox] = rec;
  const cx = (bbox[0] + bbox[2]) / 2, cy = (bbox[1] + bbox[3]) / 2;
  const files = readJSON("manifest.json").files;
  if (level !== "region") {
    const regional = files.find((f) => f.bounds && f.file.startsWith(cc.toLowerCase() + "-") &&
      cx >= f.bounds[0] && cx <= f.bounds[2] && cy >= f.bounds[1] && cy <= f.bounds[3]);
    if (regional) return regional;
  }
  return files.find((f) => f.file === "overview.pmtiles");
}

async function tilesInView(pm, zv, view, layers) {
  const out = [];
  const s = 2 ** (view.z - zv);
  const t0x = Math.floor(view.ox / s / TILE), t1x = Math.floor((view.ox + view.w) / s / TILE);
  const t0y = Math.floor(view.oy / s / TILE), t1y = Math.floor((view.oy + view.h) / s / TILE);
  const n = 2 ** zv;
  const jobs = [];
  for (let tx = t0x; tx <= t1x; tx++) for (let ty = t0y; ty <= t1y; ty++) {
    if (ty < 0 || ty >= n) continue;
    const x = ((tx % n) + n) % n;
    jobs.push(pm.getZxy(zv, x, ty).then((t) => {
      if (!t) return;
      const vt = new VectorTile(new Pbf(new Uint8Array(t.data)));
      for (const name of layers) {
        const l = vt.layers[name];
        if (!l) continue;
        for (let i = 0; i < l.length; i++) out.push({ tx, ty, layer: name, f: l.feature(i), extent: l.extent });
      }
    }).catch(() => {}));
  }
  await Promise.all(jobs);
  return { feats: out, s };
}

function featurePath(item, zv, view) {
  const { f, tx, ty, extent } = item;
  const s = 2 ** (view.z - zv);
  const rings = f.loadGeometry();
  let d = "";
  for (const ring of rings) {
    if (ring.length < (f.type === 3 ? 3 : 2)) continue;
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity, r = "";
    ring.forEach((p, i) => {
      const x = (tx + p.x / extent) * TILE * s - view.ox;
      const y = (ty + p.y / extent) * TILE * s - view.oy;
      x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
      r += (i ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1);
    });
    // resvg aborts on paths without area, so rings that collapse to a line are dropped
    if (x1 - x0 < 0.2 || y1 - y0 < 0.2) continue;
    d += r + (f.type === 3 ? "Z" : "");
  }
  return d;
}

// ---------- open orthophotos whose licences allow reuse with attribution
const IMAGERY = [
  { cc: "FR", bounds: [-5.3, 41.3, 9.6, 51.1], min: 12, max: 19, attribution: "Orthophotos © IGN France",
    url: (z, x, y) => "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/jpeg&TILEMATRIX=" + z + "&TILEROW=" + y + "&TILECOL=" + x },
  { cc: "ES", bounds: [-9.4, 35.9, 4.4, 43.9], min: 12, max: 19, attribution: "PNOA © IGN España (CC BY 4.0)",
    url: (z, x, y) => "https://www.ign.es/wmts/pnoa-ma?request=GetTile&service=WMTS&VERSION=1.0.0&Layer=OI.OrthoimageCoverage&Style=default&Format=image/jpeg&TileMatrixSet=GoogleMapsCompatible&TileMatrix=" + z + "&TileRow=" + y + "&TileCol=" + x },
  { cc: "CH", bounds: [5.95, 45.8, 10.5, 47.82], min: 12, max: 19, attribution: "SWISSIMAGE © swisstopo",
    url: (z, x, y) => "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swissimage/default/current/3857/" + z + "/" + x + "/" + y + ".jpeg" },
];

async function fetchTile(url, ms = 7000) {
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), ms);
  try {
    const r = await fetch(url, { signal: ac.signal, headers: { "User-Agent": "OpenWineAtlas/1.0 (+https://openwineatlas.com)" } });
    if (!r.ok) return null;
    const type = r.headers.get("content-type") || "image/jpeg";
    if (!type.startsWith("image/")) return null;
    return "data:" + type + ";base64," + Buffer.from(await r.arrayBuffer()).toString("base64");
  } catch (e) { return null; } finally { clearTimeout(timer); }
}

async function imageryLayer(src, view, mapH) {
  const zi = Math.max(src.min, Math.min(src.max, Math.round(view.z)));
  const s = 2 ** (view.z - zi), size = TILE * s;
  const t0x = Math.floor(view.ox / size), t1x = Math.floor((view.ox + view.w) / size);
  const t0y = Math.floor(view.oy / size), t1y = Math.floor((view.oy + mapH) / size);
  const list = [];
  for (let x = t0x; x <= t1x; x++) for (let y = t0y; y <= t1y; y++) list.push([x, y]);
  if (list.length > 90) return { svg: "", ok: 0 };
  let ok = 0;
  const parts = new Array(list.length);
  let next = 0;
  const worker = async () => {
    while (next < list.length) {
      const i = next++;
      const [x, y] = list[i];
      const uri = await fetchTile(src.url(zi, x, y));
      if (!uri) { parts[i] = ""; continue; }
      ok++;
      // a hair of overlap hides the seams between scaled tiles
      parts[i] = '<image href="' + uri + '" x="' + (x * size - view.ox).toFixed(2) + '" y="' + (y * size - view.oy).toFixed(2) +
        '" width="' + (size + 0.6).toFixed(2) + '" height="' + (size + 0.6).toFixed(2) + '" preserveAspectRatio="none"/>';
    }
  };
  await Promise.all(Array.from({ length: 10 }, worker));
  return { svg: parts.join(""), ok, total: list.length };
}

// ---------- text helpers (Cormorant and Plex have no runtime measuring here, so widths are estimated)
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
function wrap(text, maxChars, maxLines) {
  const words = String(text).split(/\s+/);
  const lines = [];
  let cur = "";
  for (const w of words) {
    const t = cur ? cur + " " + w : w;
    if (t.length <= maxChars || !cur) cur = t; else { lines.push(cur); cur = w; }
  }
  if (cur) lines.push(cur);
  if (lines.length > maxLines) {
    const keep = lines.slice(0, maxLines);
    keep[maxLines - 1] = keep[maxLines - 1].replace(/[\s,.;:]*\S*$/, "") + "…";
    return keep;
  }
  return lines;
}
function titleLines(name, width) {
  // Cormorant Garamond medium averages about 0.43 em per character
  for (const size of [112, 96, 84, 72, 62, 54]) {
    const per = Math.floor(width / (size * 0.43));
    const parts = name.length <= per ? [name] : wrap(name.replace(/-/g, "- ").replace(/- (?=\S)/g, "-​"), per, 3).map((l) => l.replace(/​/g, ""));
    if (parts.length <= 2 && !parts.some((l) => l.endsWith("…"))) return { size, lines: parts.map((l) => l.replace(/- $/, "-")) };
  }
  return { size: 54, lines: wrap(name, Math.floor(width / (54 * 0.43)), 2) };
}

const COUNTRY = { FR: "France", IT: "Italy", ES: "Spain", DE: "Germany", CH: "Switzerland", AT: "Austria", PT: "Portugal", US: "United States",
  AU: "Australia", NZ: "New Zealand", ZA: "South Africa", AR: "Argentina", CL: "Chile", GR: "Greece", HU: "Hungary", GB: "United Kingdom" };
const RANK = { grand_cru: "Grand cru", premier_cru: "Premier cru", docg: "DOCG", doca: "DOCa", pago: "Vino de Pago" };
const LEVEL = { region: "Region", appellation: "Appellation", subzone: "Sub-zone", vineyard: "Vineyard", vineyard_area: "Vineyard area" };

const fmt = (n, dp = 0) => Number(n).toLocaleString("en-GB", { maximumFractionDigits: dp, minimumFractionDigits: 0 }).replace(/,/g, " ");
function facts(d) {
  const out = [];
  const area = d.area_ha ?? d.outline_area_ha;
  if (area != null) out.push(["Area", fmt(area, area < 100 ? 1 : 0) + " ha"]);
  const towns = d.gemarkungen?.length ? d.gemarkungen : d.communes;
  if (towns?.length) out.push([towns.length === 1 ? "Commune" : "Communes", towns.length <= 1 ? towns[0] : String(towns.length)]);
  const mains = [...new Set((d.wines || []).flatMap((w) => w.main || []))].map((g) => g.replace(/\s+(N|B|G|Rs|Rg)$/, ""));
  if (mains.length && mains.length <= 2) out.push([mains.length === 1 ? "Grape" : "Grapes", mains.join(" · ")]);
  else if (d.grapes && !mains.length) { const g = d.grapes.split("/").map((x) => x.replace(/\s+(N|B|G|Rs|Rg)$/, "").trim()); if (g.length <= 2) out.push([g.length === 1 ? "Grape" : "Grapes", g.join(" · ")]); }
  if (d.bedrock?.length) {
    // "Carbonate sedimentary rocks (limestone, marl, dolomite)" reads best as its first examples
    const [rock, pct] = d.bedrock[0];
    const m = rock.match(/\(([^)]+)\)/);
    const label = m ? m[1].split(",").slice(0, 2).map((x) => x.trim()).join(", ") : rock;
    out.push(["Bedrock", label.charAt(0).toUpperCase() + label.slice(1) + (pct && pct < 100 ? " " + pct + "%" : "")]);
  }
  if (d.registered) out.push(["Protected since", String(d.registered).slice(0, 4)]);
  if (d.plots > 1) out.push(["Separate plots", String(d.plots)]);
  if (d.max_yield_hl_ha) out.push(["Max. yield", fmt(d.max_yield_hl_ha, 1) + " hl/ha"]);
  return out;
}

function scaleBar(view, lat, x, y) {
  const mpp = (156543.03392 * Math.cos((lat * Math.PI) / 180)) / 2 ** view.z;
  const nice = [50, 100, 200, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000];
  const m = nice.find((v) => v / mpp >= 150) || nice[nice.length - 1];
  const px = m / mpp;
  const label = m >= 1000 ? m / 1000 + " km" : m + " m";
  return '<g font-family="IBM Plex Mono" font-size="22" fill="' + C.parchment + '">' +
    '<rect x="' + x + '" y="' + (y - 6) + '" width="' + px.toFixed(1) + '" height="6" fill="' + C.parchment + '"/>' +
    '<text x="' + (x + px + 16).toFixed(1) + '" y="' + y + '">' + label + "</text></g>";
}

// ---------- the picture
async function render(rec, d, format) {
  const F = FORMATS[format] || FORMATS.story;
  const [name, id, cc, level, rank, parent, bbox] = rec;
  const accent = TOP.has(rank) ? C.gold : rank === "premier_cru" ? C.copper : level === "vineyard" && cc === "DE" ? C.slate : C.parchment;
  const [fx0, fy0, fx1, fy1] = F.fit;
  const fw = fx1 - fx0, fh = fy1 - fy0;

  // zoom that fits the outline into the frame
  const bw = Math.max(1e-6, wx(bbox[2], 0) - wx(bbox[0], 0)), bh = Math.max(1e-6, wy(bbox[1], 0) - wy(bbox[3], 0));
  let z = Math.log2(Math.min(fw / bw, fh / bh));
  z = Math.max(3, Math.min(17.5, z));
  const ccx = wx((bbox[0] + bbox[2]) / 2, z), ccy = (wy(bbox[1], z) + wy(bbox[3], z)) / 2;
  const view = { z, ox: ccx - (fx0 + fw / 2), oy: ccy - (fy0 + fh / 2), w: F.w, h: F.mapH };
  const cLon = (bbox[0] + bbox[2]) / 2, cLat = (bbox[1] + bbox[3]) / 2;

  // basemap: open orthophotos close up, the atlas' dark land otherwise
  let base = "", attribution = [];
  const src = IMAGERY.find((s) => s.cc === cc && cLon >= s.bounds[0] && cLon <= s.bounds[2] && cLat >= s.bounds[1] && cLat <= s.bounds[3]);
  let photo = false;
  if (src && z >= src.min - 0.5) {
    const im = await imageryLayer(src, view, F.mapH);
    if (im.ok >= Math.ceil(im.total * 0.6)) { base = im.svg; photo = true; attribution.push(src.attribution); }
  }
  if (!photo && z >= 9) {
    // close in, the frame sits inside one country: plain land, as the atlas draws it
    base = '<rect width="' + F.w + '" height="' + F.mapH + '" fill="' + C.land + '"/>';
  } else if (!photo) {
    const pm = pmtiles("base.pmtiles");
    const zv = Math.max(0, Math.min(8, Math.floor(z)));
    const { feats } = await tilesInView(pm, zv, view, ["countries", "lakes"]);
    const groups = new Map();
    for (const it of feats) {
      const k = it.tx + "_" + it.ty;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(it);
    }
    base = '<rect width="' + F.w + '" height="' + F.mapH + '" fill="' + C.night + '"/>';
    for (const [k, items] of groups) {
      const [tx, ty] = k.split("_").map(Number);
      const s = 2 ** (z - zv);
      base += '<clipPath id="b' + k + '"><rect x="' + (tx * TILE * s - view.ox).toFixed(1) + '" y="' + (ty * TILE * s - view.oy).toFixed(1) + '" width="' + (TILE * s).toFixed(1) + '" height="' + (TILE * s).toFixed(1) + '"/></clipPath>';
      base += '<g clip-path="url(#b' + k + ')">' + items.map((it) => {
        const dp = featurePath(it, zv, view);
        return dp ? '<path d="' + dp + '" fill="' + (it.layer === "lakes" ? C.night : C.land) + '" fill-rule="evenodd"/>' : "";
      }).join("") + "</g>";
    }
  }

  // outlines: the place in its accent colour, its neighbours as quiet context
  const vs = vectorSourceFor(rec);
  const pm = pmtiles(vs.file);
  const zv = Math.max(vs.minzoom, Math.min(vs.maxzoom, Math.floor(z)));
  const layers = vs.file === "overview.pmtiles" ? ["appellations"] : ["appellations", "crus", "grosslagen"];
  const { feats, s } = await tilesInView(pm, zv, view, layers);
  const byTile = new Map();
  let found = false;
  for (const it of feats) {
    if (it.f.type !== 3) continue;
    const k = it.tx + "_" + it.ty;
    if (!byTile.has(k)) byTile.set(k, { ctx: "", hit: "" });
    const g = byTile.get(k);
    const dpath = featurePath(it, zv, view);
    if (!dpath) continue;
    if (it.f.properties.id === id) { g.hit += dpath; found = true; }
    else if (it.layer !== "grosslagen") g.ctx += dpath;
  }
  let outlines = "";
  for (const [k, g] of byTile) {
    const [tx, ty] = k.split("_").map(Number);
    outlines += '<clipPath id="t' + k + '"><rect x="' + (tx * TILE * s - view.ox).toFixed(1) + '" y="' + (ty * TILE * s - view.oy).toFixed(1) + '" width="' + (TILE * s).toFixed(1) + '" height="' + (TILE * s).toFixed(1) + '"/></clipPath>' +
      '<g clip-path="url(#t' + k + ')">' +
      (g.ctx ? '<path d="' + g.ctx + '" fill="none" stroke="' + C.parchment + '" stroke-opacity="' + (photo ? 0.55 : 0.3) + '" stroke-width="1.6"/>' : "") +
      (g.hit ? '<path d="' + g.hit + '" fill="' + accent + '" fill-opacity="' + (photo ? 0.22 : 0.16) + '" fill-rule="evenodd"/>' +
        (photo ? '<path d="' + g.hit + '" fill="none" stroke="#000" stroke-opacity=".45" stroke-width="9" stroke-linejoin="round"/>' : "") +
        '<path d="' + g.hit + '" fill="none" stroke="' + accent + '" stroke-width="4.5" stroke-linejoin="round"/>' : "") + "</g>";
  }
  if (!found) {
    const px = wx(cLon, z) - view.ox, py = wy(cLat, z) - view.oy;
    outlines += '<circle cx="' + px.toFixed(1) + '" cy="' + py.toFixed(1) + '" r="16" fill="' + accent + '" stroke="#000" stroke-opacity=".5" stroke-width="5"/>';
  }
  attribution.push(sourceLabel(id));

  // text
  const ctry = COUNTRY[cc] || cc;
  const kind = d.type || LEVEL[level] || "Place";
  const eyebrow = [ctry, kind, RANK[rank]].filter(Boolean).join("  ·  ").toUpperCase();
  const T = titleLines(name, F.w - 160);
  const top = F.safeTop + 6;
  let head = '<text x="80" y="' + (top + 26) + '" font-family="IBM Plex Mono" font-size="26" letter-spacing="3" fill="' + accent + '">' + esc(eyebrow) + "</text>";
  T.lines.forEach((l, i) => {
    head += '<text x="76" y="' + (top + 40 + T.size * 0.95 * (i + 1)).toFixed(0) + '" font-family="Cormorant Garamond" font-weight="500" font-size="' + T.size + '" fill="' + C.parchment + '">' + esc(l) + "</text>";
  });
  const afterTitle = top + 40 + T.size * 0.95 * T.lines.length;
  if (parent) head += '<text x="80" y="' + (afterTitle + 46).toFixed(0) + '" font-family="IBM Plex Sans" font-size="28" fill="' + C.muted + '">Part of ' + esc(parent) + "</text>";

  const list = facts(d).slice(0, format === "square" ? 2 : 4);
  const note = d.atlas_note && format !== "square" ? wrap(d.atlas_note, 52, format === "story" ? 4 : 2) : [];
  let low = "";
  let y = F.mapH + (format === "story" ? 20 : 10);
  if (format === "square") y = F.h - 230;
  note.forEach((l, i) => { low += '<text x="80" y="' + (y + 40 * (i + 1)) + '" font-family="Cormorant Garamond" font-style="italic" font-weight="500" font-size="40" fill="' + C.parchment + '">' + esc(l) + "</text>"; });
  if (note.length) y += 40 * note.length + 46;
  list.forEach(([k, v], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 80 + col * 470, yy = y + row * 112;
    low += '<text x="' + x + '" y="' + (yy + 26) + '" font-family="IBM Plex Mono" font-size="22" letter-spacing="2" fill="' + C.muted + '">' + esc(k.toUpperCase()) + "</text>" +
      '<text x="' + x + '" y="' + (yy + 76) + '" font-family="IBM Plex Mono" font-weight="500" font-size="' + Math.min(38, Math.floor(440 / (0.6 * v.length))) + '" fill="' + C.parchment + '">' + esc(v) + "</text>";
  });
  const footY = format === "story" ? 1650 : F.h - 48;

  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + F.w + '" height="' + F.h + '" viewBox="0 0 ' + F.w + " " + F.h + '">' +
    "<defs>" +
    '<linearGradient id="gt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + C.night + '" stop-opacity=".92"/><stop offset=".55" stop-color="' + C.night + '" stop-opacity=".55"/><stop offset="1" stop-color="' + C.night + '" stop-opacity="0"/></linearGradient>' +
    '<linearGradient id="gb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + C.night + '" stop-opacity="0"/><stop offset="1" stop-color="' + C.night + '" stop-opacity="1"/></linearGradient>' +
    "</defs>" +
    '<rect width="' + F.w + '" height="' + F.h + '" fill="' + C.night + '"/>' +
    // resvg mishandles tile clips nested in a second clip, so the map is masked by painting below it instead
    base + outlines +
    (F.mapH < F.h ? '<rect y="' + F.mapH + '" width="' + F.w + '" height="' + (F.h - F.mapH) + '" fill="' + C.night + '"/>' : "") +
    '<rect width="' + F.w + '" height="' + Math.round(afterTitle + 140) + '" fill="url(#gt)"/>' +
    (format === "square" ? '<rect y="' + (F.h - 380) + '" width="' + F.w + '" height="380" fill="url(#gb)"/>' : '<rect y="' + (F.mapH - 260) + '" width="' + F.w + '" height="261" fill="url(#gb)"/>') +
    scaleBar(view, cLat, 80, (format === "square" ? F.h - 300 : F.mapH - 70)) +
    '<text x="' + (F.w - 80) + '" y="' + (format === "square" ? F.h - 300 : F.mapH - 70) + '" text-anchor="end" font-family="IBM Plex Mono" font-size="17" fill="' + C.parchment + '" fill-opacity=".8">' + esc(attribution.filter(Boolean).join(" · ")) + "</text>" +
    head + low +
    '<text x="80" y="' + footY + '" font-family="Cormorant Garamond" font-weight="500" font-size="36" fill="' + C.parchment + '">Open Wine Atlas</text>' +
    '<text x="' + (F.w - 80) + '" y="' + footY + '" text-anchor="end" font-family="IBM Plex Mono" font-size="24" fill="' + C.muted + '">openwineatlas.com</text>' +
    "</svg>";

  if (process.env.OWA_DEBUG_SVG) fs.writeFileSync(process.env.OWA_DEBUG_SVG, svg);
  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: F.w },
    font: { loadSystemFonts: false, defaultFontFamily: "IBM Plex Sans",
      fontFiles: fs.readdirSync(FONTS).filter((f) => f.endsWith(".ttf")).map((f) => path.join(FONTS, f)) },
  });
  return { png: resvg.render().asPng(), photo, found };
}

function sourceLabel(id) {
  const src = id.split("-")[1];
  return { inao: "Outline INAO", eupdo: "Outline Candiago et al. 2022", ava: "Outline UC Davis AVA", rlp: "Outline LWK Rheinland-Pfalz",
    ch: "Outline BFS/swisstopo", world: "Outline geoBoundaries", osm: "© OpenStreetMap" }[src] || "";
}

export default async function handler(req, res) {
  try {
    const u = new URL(req.url, "http://x");
    // a trailing .png lets tools that sniff the extension accept /story/<id>.png
    const rec = findPlace((u.searchParams.get("id") || "").replace(/\.png$/i, ""), u.searchParams.get("q"));
    if (!rec) { res.statusCode = 404; res.setHeader("Content-Type", "text/plain"); return res.end("Place not found. Use ?id=<atlas id> or ?q=<name>."); }
    const format = FORMATS[u.searchParams.get("format")] ? u.searchParams.get("format") : "story";
    const details = (() => { try { return readJSON("details-" + rec[2].toLowerCase() + ".json")[rec[1]] || {}; } catch (e) { return {}; } })();
    const { png, photo } = await render(rec, details, format);
    res.statusCode = 200;
    res.setHeader("Content-Type", "image/png");
    res.setHeader("Content-Disposition", 'inline; filename="' + rec[1] + "-" + format + '.png"');
    // a day at the edge; a failed photo fetch is cached only briefly so the next request tries again
    res.setHeader("Cache-Control", photo || !rec ? "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800" : "public, max-age=300, s-maxage=600");
    res.end(png);
  } catch (e) {
    res.statusCode = 500;
    res.setHeader("Content-Type", "text/plain");
    res.end("Could not render this place.");
    console.error(e);
  }
}
