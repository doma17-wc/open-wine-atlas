// Two to eight places drawn at the same scale, side by side, as an SVG: the picture of the comparison reels.
//   /api/pair?ids=<place id>,<place id>[,…]      (&theme=light for a light background)
// The outlines are read from the same PMTiles archives as the map, at a zoom that keeps each one sharp, then put
// on one ground scale (metres, corrected for latitude), so Oakville and Pauillac compare even though they are an
// ocean apart. The map's sheet shows it under "Drawn at the same scale".
import fs from "node:fs";
import path from "node:path";
import { PMTiles } from "pmtiles";
import { VectorTile } from "@mapbox/vector-tile";
import Pbf from "pbf";

const ROOT = process.cwd();
const DATA = path.join(ROOT, "web", "data");
const THEMES = {
  dark: { bg: "#0b0b0d", fill: "#e7c06a", text: "#e6dccb", muted: "#8d877c" },
  light: { bg: "#f1ebdf", fill: "#a77b2c", text: "#1d1b18", muted: "#6f685d" },
};
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
const byId = () => once("byId", () => new Map(readJSON("search.json").map((r) => [r[1], r])));

const TILE = 256, EARTH = 40075016.686;
const tileX = (lon, z) => Math.floor(((lon + 180) / 360) * 2 ** z);
const tileY = (lat, z) => { const s = Math.sin((lat * Math.PI) / 180); return Math.floor((0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * 2 ** z); };

// the archives that may hold the place in detail (regional boxes overlap), then the world overview
function sourcesFor(rec) {
  const [, , cc, level, , , b] = rec;
  const cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
  const files = readJSON("manifest.json").files;
  const regional = level === "region" ? [] : files.filter((f) => f.bounds && f.file.startsWith(cc.toLowerCase() + "-") &&
    cx >= f.bounds[0] && cx <= f.bounds[2] && cy >= f.bounds[1] && cy <= f.bounds[3]);
  return [...regional, files.find((f) => f.file === "overview.pmtiles")];
}

// the outline of one place as rings in metres on the ground, around its own centre
async function outline(rec) {
  for (const src of sourcesFor(rec)) {
    const o = await outlineFrom(rec, src);
    if (o) return o;
  }
  return null;
}
async function outlineFrom(rec, src) {
  const [, id, , , , , b] = rec;
  // about 600 px across the place, within the zooms of the archive, and never more than 36 tiles
  const span = Math.max(1e-6, (b[2] - b[0]) / 360, (b[3] - b[1]) / 180);
  let z = Math.round(Math.log2(600 / TILE / span));
  z = Math.max(src.minzoom, Math.min(src.maxzoom, z));
  while (z > src.minzoom && (tileX(b[2], z) - tileX(b[0], z) + 1) * (tileY(b[1], z) - tileY(b[3], z) + 1) > 36) z--;
  const layers = src.file === "overview.pmtiles" ? ["appellations"] : ["appellations", "crus", "grosslagen"];
  const pm = pmtiles(src.file), jobs = [], rings = [];
  for (let tx = tileX(b[0], z); tx <= tileX(b[2], z); tx++) for (let ty = tileY(b[3], z); ty <= tileY(b[1], z); ty++) {
    jobs.push(pm.getZxy(z, tx, ty).then((t) => {
      if (!t) return;
      const vt = new VectorTile(new Pbf(new Uint8Array(t.data)));
      for (const name of layers) {
        const l = vt.layers[name];
        if (!l) continue;
        for (let i = 0; i < l.length; i++) {
          const f = l.feature(i);
          if (f.type !== 3 || f.properties.id !== id) continue;
          // one feature of one tile is one path: its holes cut with even-odd, while the pieces of the same place in
          // neighbouring tiles (which overlap by the tile buffer) are separate paths, so the overlap does not cut a hole
          const part = f.loadGeometry().filter((ring) => ring.length > 2).map((ring) => ring.map((p) => [(tx + p.x / l.extent) * TILE, (ty + p.y / l.extent) * TILE]));
          if (part.length) rings.push(part);
        }
      }
    }).catch(() => {}));
  }
  await Promise.all(jobs);
  if (!rings.length) return null;
  // world pixels at zoom z to metres on the ground at the latitude of the place
  const lat = (b[1] + b[3]) / 2, m = (EARTH / (TILE * 2 ** z)) * Math.cos((lat * Math.PI) / 180);
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const part of rings) for (const ring of part) for (const [x, y] of ring) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  return { parts: rings.map((part) => part.map((r) => r.map(([x, y]) => [(x - x0) * m, (y - y0) * m]))), w: (x1 - x0) * m, h: (y1 - y0) * m };
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const short = (name, parent) => parent && name.startsWith(parent + " ") ? name.slice(parent.length + 1).replace(/^(premier|grand) cru /, "") : name;

async function render(recs, theme) {
  const T = THEMES[theme] || THEMES.dark;
  const shapes = await Promise.all(recs.map(outline));
  const n = recs.length, CW = n === 2 ? 300 : 200, CH = 240, GAP = 24, PAD = 16, LAB = 44;
  const W = PAD * 2 + n * CW + (n - 1) * GAP, H = PAD + CH + LAB + 28;
  const ok = shapes.filter(Boolean);
  const s = ok.length ? Math.min(...ok.map((p) => Math.min(CW / Math.max(p.w, 1), CH / Math.max(p.h, 1)))) : 1;
  let body = "";
  recs.forEach((r, i) => {
    const p = shapes[i], cx = PAD + i * (CW + GAP);
    if (p) {
      const ox = cx + (CW - p.w * s) / 2, oy = PAD + (CH - p.h * s);
      // a hairline of the same colour closes the seams that anti-aliasing leaves between parcels and tiles
      body += '<g fill="' + T.fill + '" stroke="' + T.fill + '" stroke-width="0.6" stroke-linejoin="round" fill-rule="evenodd">' + p.parts.map((part) =>
        '<path d="' + part.map((ring) => "M" + ring.map(([x, y]) => (x * s + ox).toFixed(1) + " " + (y * s + oy).toFixed(1)).join("L") + "Z").join("") + '"/>').join("") + "</g>";
    }
    const name = short(r[0], r[5]);
    body += '<text x="' + (cx + CW / 2) + '" y="' + (PAD + CH + 24) + '" text-anchor="middle" font-family="Georgia,serif" font-size="20" fill="' + T.text + '">' + esc(name.length > 26 ? name.slice(0, 25) + "…" : name) + "</text>";
  });
  // a scale bar of a round length
  const len = [50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000].filter((v) => v * s <= 120).pop() || 50;
  const y = H - 12;
  body += '<line x1="' + PAD + '" y1="' + y + '" x2="' + (PAD + len * s).toFixed(1) + '" y2="' + y + '" stroke="' + T.muted + '" stroke-width="2"/>' +
    '<text x="' + (PAD + len * s + 8).toFixed(1) + '" y="' + (y + 4) + '" font-family="Menlo,monospace" font-size="12" fill="' + T.muted + '">' + (len < 1000 ? len + " m" : len / 1000 + " km") + "</text>" +
    '<text x="' + (W - PAD) + '" y="' + (y + 4) + '" text-anchor="end" font-family="Menlo,monospace" font-size="12" fill="' + T.muted + '">Same scale · openwineatlas.com</text>';
  return { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + " " + H + '" width="' + W + '" height="' + H + '">' +
    '<rect width="100%" height="100%" fill="' + T.bg + '"/>' + body + "</svg>", missing: shapes.some((p) => !p) };
}

export default async function handler(req, res) {
  try {
    const u = new URL(req.url, "http://x");
    const ids = [...new Set((u.searchParams.get("ids") || "").split(",").map((s) => s.trim()).filter(Boolean))];
    const recs = ids.map((id) => byId().get(id)).filter(Boolean);
    if (recs.length < 2 || recs.length > 8 || recs.length !== ids.length) {
      res.statusCode = 400; res.setHeader("Content-Type", "text/plain");
      return res.end("Give two to eight atlas place ids: /api/pair?ids=<id>,<id>");
    }
    const { svg, missing } = await render(recs, u.searchParams.get("theme"));
    res.statusCode = 200;
    res.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
    res.setHeader("Cache-Control", missing ? "public, max-age=300" : "public, max-age=86400, s-maxage=604800, stale-while-revalidate=604800");
    res.end(svg);
  } catch (e) {
    res.statusCode = 500; res.setHeader("Content-Type", "text/plain");
    res.end("Could not draw these places.");
    console.error(e);
  }
}
