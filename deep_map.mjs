// Deep dive, pass 1: map footage, one folder of frames per shot, from the real atlas page.
// usage: node deep_map.mjs spec.json outdir [shotIndex]
// Each shot: {dur, cam:[[t,lng,lat,zoom,bearing,pitch],...], layers:{alt,slope,aspect,rivers}, labels:true|false, pad:{top,bottom}}
// Frames are rendered at spec.fpsMap (default 10) and later interpolated to 30 fps per shot, so cuts stay clean.
import fs from "node:fs";
import path from "node:path";
import { openAtlas, idle } from "./page.mjs";

const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = process.argv[3];
const only = process.argv[4] != null ? +process.argv[4] : null;
const FPS = spec.fpsMap || 10;

const { browser, page } = await openAtlas({ hash: spec.id || "", css: "#ovl{display:none!important}", globe: spec.globe !== false, labelScale: spec.labelScale || 1.55 });

// markers: small gold dots with a label, drawn as map layers so they sit on the terrain
if (spec.markers && spec.markers.length) {
  await page.evaluate((mk) => {
    const m = window.__map;
    m.addSource("dd-mk", { type: "geojson", data: { type: "FeatureCollection", features: mk.map((x, i) => ({ type: "Feature", id: i,
      properties: { label: x.label, shot: x.shots ? x.shots.join(",") : "" }, geometry: { type: "Point", coordinates: [x.lng, x.lat] } })) } });
    m.addLayer({ id: "dd-mk-halo", type: "circle", source: "dd-mk", layout: { visibility: "none" },
      paint: { "circle-radius": 11, "circle-color": "rgba(231,192,106,0.25)", "circle-stroke-width": 0 } });
    m.addLayer({ id: "dd-mk-dot", type: "circle", source: "dd-mk", layout: { visibility: "none" },
      paint: { "circle-radius": 5, "circle-color": "#efc96f", "circle-stroke-width": 2, "circle-stroke-color": "#0b0b0d" } });
    m.addLayer({ id: "dd-mk-lbl", type: "symbol", source: "dd-mk", layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Regular"],
      "text-size": 21, "text-offset": [0, -1.25], "text-anchor": "bottom", "text-allow-overlap": true, "text-ignore-placement": false },
      paint: { "text-color": "#f6e3b4", "text-halo-color": "rgba(10,10,12,0.95)", "text-halo-width": 2.2 } });
  }, spec.markers);
}

// wait until every tile of the view is in and drawn (much faster than the map's own idle event, which also waits for fades)
async function settle(timeout = 30000) {
  await page.evaluate((timeout) => new Promise((res) => {
    const m = window.__map, t0 = performance.now();
    const check = () => { if ((m.areTilesLoaded() && m.loaded()) || performance.now() - t0 > timeout) res(); else setTimeout(check, 25); };
    m.once("render", () => setTimeout(check, 0)); m.triggerRepaint();
  }), timeout);
}
await page.evaluate(() => { const m = window.__map; m._fadeDuration = 0; try { m.style.setTransition({ duration: 0, delay: 0 }); } catch (e) {} });

const ease = (x) => x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
function cam(K, t) {
  if (t <= K[0][0]) return K[0];
  for (let i = 0; i < K.length - 1; i++) {
    const a = K[i], b = K[i + 1];
    if (t >= a[0] && t <= b[0]) {
      const u = (b[0] - a[0]) > 4 ? (t - a[0]) / (b[0] - a[0]) * 0.15 + ease((t - a[0]) / (b[0] - a[0])) * 0.85 : ease((t - a[0]) / (b[0] - a[0]));
      const uc = Math.min(1, u * (b[3] > a[3] + 2 ? 1.35 : 1));
      return [t, a[1] + (b[1] - a[1]) * uc, a[2] + (b[2] - a[2]) * uc, a[3] + (b[3] - a[3]) * u, a[4] + (b[4] - a[4]) * u, a[5] + (b[5] - a[5]) * u];
    }
  }
  return K[K.length - 1];
}

const LAYER_IDS = { alt: ["alt"], slope: ["slope"], aspect: ["aspect"] };
async function setLayers(shot, idx) {
  await page.evaluate((L, labels, idx, ids) => {
    const m = window.__map;
    for (const [k, list] of Object.entries(ids)) for (const id of list) if (m.getLayer(id)) m.setLayoutProperty(id, "visibility", L[k] ? "visible" : "none");
    if (L.altOpacity != null && m.getLayer("alt")) m.setPaintProperty("alt", "color-relief-opacity", L.altOpacity);
    // labels off gives a clean plate under a busy chart
    for (const id of ["wineries"]) if (m.getLayer(id)) m.setLayoutProperty(id, "visibility", L.wineries ? "visible" : "none");
    for (const l of m.getStyle().layers) {
      if (l.type !== "symbol" || l.id.startsWith("dd-mk")) continue;
      if (/winer|poi|producer|estate/i.test(l.id)) { m.setLayoutProperty(l.id, "visibility", "none"); continue; }
      m.setLayoutProperty(l.id, "visibility", labels ? "visible" : "none");
    }
    const show = !!L.markers;
    for (const id of ["dd-mk-halo", "dd-mk-dot", "dd-mk-lbl"]) if (m.getLayer(id)) {
      m.setLayoutProperty(id, "visibility", show ? "visible" : "none");
      m.setFilter(id, ["any", ["==", ["get", "shot"], ""], ["in", String(idx), ["get", "shot"]]]);
    }
  }, shot.layers || {}, shot.labels !== false, idx, LAYER_IDS);
}

const t0 = Date.now();
for (let i = 0; i < spec.shots.length; i++) {
  if (only != null && i !== only) continue;
  const shot = spec.shots[i];
  const dir = path.join(out, "shot" + String(i).padStart(2, "0"));
  fs.mkdirSync(dir, { recursive: true });
  const SF = shot.fps || FPS;
  const n = Math.round(shot.dur * SF) + 1;
  if (fs.existsSync(path.join(dir, String(n - 1).padStart(5, "0") + ".jpg"))) { console.log("shot", i, "done already"); continue; }
  await setLayers(shot, i);
  await page.evaluate((g, ex) => { const m = window.__map; const want = g ? "globe" : "mercator";
    if ((m.getProjection()?.type || "mercator") !== want) m.setProjection({ type: want });
    // real 3D relief for the low, tilted shots (the atlas' own dem3d source)
    if (ex && m.getSource("dem3d")) m.setTerrain({ source: "dem3d", exaggeration: ex }); else m.setTerrain(null);
  }, !!shot.globe, shot.terrain || 0);
  const P = shot.pad || { top: 0, bottom: 0 };
  const padding = { top: P.top || 0, bottom: P.bottom || 0, left: 0, right: 0 };
  // warm the tiles at every keyframe of the shot
  for (const k of shot.cam) {
    await page.evaluate((k, p) => window.__map.jumpTo({ center: [k[1], k[2]], zoom: k[3], bearing: k[4], pitch: k[5], padding: p }), k, padding);
    await idle(page, 60000);
  }
  await settle(60000);
  // the atlas can re-show layers while tiles load: apply the shot's layer settings again before recording
  await setLayers(shot, i);
  await settle(20000);
  for (let f = 0; f < n; f++) {
    const file = path.join(dir, String(f).padStart(5, "0") + ".jpg");
    if (fs.existsSync(file)) continue;
    const c = cam(shot.cam, f / SF);
    await page.evaluate((c, p) => window.__map.jumpTo({ center: [c[1], c[2]], zoom: c[3], bearing: c[4], pitch: c[5], padding: p }), c, padding);
    await settle(20000);
    await page.screenshot({ path: file, type: "jpeg", quality: 92, optimizeForSpeed: true });
  }
  console.log("shot", i, n, "frames", ((Date.now() - t0) / 1000).toFixed(0), "s");
}
await browser.close();
