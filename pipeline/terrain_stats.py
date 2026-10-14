"""Elevation, slope and aspect of every place, measured once and stored with its details.

The map measures the terrain of a place live in the browser when it is opened. This script runs the same
measurement for every place in the atlas ahead of time, so that the figures can be sorted and ranked (the
Records view: highest, steepest …), printed on the static pages and used without a browser.

Method (as in measureTerrain() of web/index.src.html):
  * the outline is read from the published vector tiles (web/data/*.pmtiles);
  * the Mapterhorn elevation tiles (terrarium encoding, 512 px) are read at the finest zoom that keeps a place to
    a few tiles, the outline is rasterised on that grid and every cell inside it is used;
  * slope and aspect come from a 3 x 3 Sobel kernel; aspect is the compass direction the ground faces.

Stored in details-<cc>.json as
  terrain: {e: [min, mean, max, p10, p90] m, s: [mean, p90] degrees or null, asp: mean aspect in degrees or null,
            dom: dominant 45° sector, flat: share under 2°, res: cell size in m, n: cells}
Slope and aspect are only stored when the cells are 35 m or finer; on coarser grids they mean little.

Run:  python pipeline/terrain_stats.py           (tiles are cached in raw/dem/, so a rerun is quick)
      python pipeline/terrain_stats.py --only FR  (one country)
"""
import argparse
import glob
import gzip
import io
import json
import math
import os
import threading
import ssl
import urllib.error
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import mapbox_vector_tile
import numpy as np
from PIL import Image, ImageDraw
from pmtiles.reader import MmapSource, Reader

from common import RAW, ROOT

DATA = os.path.join(ROOT, "web", "data")
DEM_URL = "https://tiles.mapterhorn.com/{z}/{x}/{y}.webp"
DEM_TILE, DEM_MAX = 512, 14
CACHE = os.path.join(RAW, "dem")
SECTORS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
# behind a TLS-inspecting proxy the system store may not know its CA; honour the usual variables
_ca = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
UA = {"User-Agent": "open-wine-atlas terrain_stats (+https://openwineatlas.com)"}
SSL = ssl.create_default_context(cafile=_ca) if _ca and os.path.exists(_ca) else ssl.create_default_context()


def merc(lon, lat):
    x = (lon + 180) / 360
    y = (1 - math.asinh(math.tan(math.radians(max(-85, min(85, lat))))) / math.pi) / 2
    return x, y


# ---------------------------------------------------------------- vector tiles
class Tiles:
    def __init__(self):
        self.files = {}
        self.decoded = {}
        self.lock = threading.Lock()
        man = json.load(open(os.path.join(DATA, "manifest.json"), encoding="utf-8"))
        self.detail = [f for f in man["files"] if f["file"].startswith(("fr-", "de-"))]

    def reader(self, name):
        with self.lock:
            if name not in self.files:
                fh = open(os.path.join(DATA, name), "rb")
                r = Reader(MmapSource(fh))
                h = r.header()
                self.files[name] = (r, h["min_zoom"], h["max_zoom"], threading.Lock())
            return self.files[name]

    def tile(self, name, z, x, y):
        key = (name, z, x, y)
        if key in self.decoded:
            return self.decoded[key]
        t = self._tile(name, z, x, y)
        if len(self.decoded) > 400:
            self.decoded.pop(next(iter(self.decoded)), None)
        self.decoded[key] = t
        return t

    def _tile(self, name, z, x, y):
        r, _, _, lk = self.reader(name)
        with lk:
            d = r.get(z, x, y)
        if not d:
            return None
        if d[:2] == b"\x1f\x8b":
            d = gzip.decompress(d)
        return mapbox_vector_tile.decode(d, default_options={"y_coord_down": True})

    def files_for(self, pid, bbox):
        cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
        if pid.startswith("de-rlp-"):
            return ["de-rlp.pmtiles"]
        if pid.startswith("fr-inao-"):
            hit = [f["file"] for f in self.detail if f["file"].startswith("fr-") and f["bounds"]
                   and f["bounds"][0] <= cx <= f["bounds"][2] and f["bounds"][1] <= cy <= f["bounds"][3]]
            return hit + ["overview.pmtiles"]
        return ["overview.pmtiles"]

    def outline(self, pid, bbox):
        """Polygon rings in mercator unit coordinates (0..1), gathered from the tiles over the box."""
        x0, y1 = merc(bbox[0], bbox[1])
        x1, y0 = merc(bbox[2], bbox[3])
        for name in self.files_for(pid, bbox):
            _, zmin, zmax, _ = self.reader(name)
            z = zmax
            while z > zmin:
                n = 2 ** z
                if (int(x1 * n) - int(x0 * n) + 1) * (int(y1 * n) - int(y0 * n) + 1) <= 4:
                    break
                z -= 1
            n = 2 ** z
            polys = []
            for tx in range(int(x0 * n), int(x1 * n) + 1):
                for ty in range(int(y0 * n), int(y1 * n) + 1):
                    t = self.tile(name, z, tx, ty)
                    if not t:
                        continue
                    for layer in ("appellations", "crus", "grosslagen"):
                        if layer not in t:
                            continue
                        ext = t[layer]["extent"]
                        for ft in t[layer]["features"]:
                            if ft["properties"].get("id") != pid:
                                continue
                            g = ft["geometry"]
                            parts = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"] if g["type"] == "MultiPolygon" else []
                            for poly in parts:
                                rings = [[((tx + min(max(px, 0), ext) / ext) / n, (ty + min(max(py, 0), ext) / ext) / n) for px, py in ring] for ring in poly]
                                polys.append(rings)
            if polys:
                return polys
        return []


# ---------------------------------------------------------------- elevation tiles
_dem_lock = threading.Lock()


def dem_tile(z, x, y):
    path = os.path.join(CACHE, str(z), str(x), f"{y}.webp")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        url = DEM_URL.format(z=z, x=x, y=y)
        data = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60, context=SSL) as resp:
                    data = resp.read()
                break
            except urllib.error.HTTPError as ex:
                if ex.code == 404:  # no tile there (open sea): remember it as empty
                    data = b""
                    break
            except Exception:
                pass
        if data is None:
            return None  # network trouble: do not cache, the next run tries again
        tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"  # two threads may fetch the same tile
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    data = open(path, "rb").read()
    if not data:
        return None
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    a = np.asarray(im, dtype=np.float32)
    e = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    e[a[..., 3] == 0] = np.nan
    return e


def measure(polys, vineyard):
    xs = [p[0] for poly in polys for p in poly[0]]
    ys = [p[1] for poly in polys for p in poly[0]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    limit = 6 if vineyard else 4
    z = DEM_MAX
    while z >= 4:
        n = 2 ** z
        tx0, ty0 = int(x0 * n), int(y0 * n)
        nx, ny = int(x1 * n) - tx0 + 1, int(y1 * n) - ty0 + 1
        if nx * ny <= limit:
            break
        z -= 1
    W, H = nx * DEM_TILE, ny * DEM_TILE
    elev = np.full((H, W), np.nan, dtype=np.float32)
    ok = False
    for j in range(ny):
        for i in range(nx):
            t = dem_tile(z, tx0 + i, ty0 + j)
            if t is not None:
                elev[j * DEM_TILE:(j + 1) * DEM_TILE, i * DEM_TILE:(i + 1) * DEM_TILE] = t
                ok = True
    if not ok:
        return None
    scale, ox, oy = 2 ** z * DEM_TILE, tx0 * DEM_TILE, ty0 * DEM_TILE
    mask_im = Image.new("1", (W, H), 0)
    dr = ImageDraw.Draw(mask_im)
    for poly in polys:
        rings = [[(px * scale - ox, py * scale - oy) for px, py in ring] for ring in poly]
        if len(rings[0]) >= 3:
            dr.polygon(rings[0], fill=1)
        for hole in rings[1:]:
            if len(hole) >= 3:
                dr.polygon(hole, fill=0)
    mask = np.array(mask_im, dtype=bool)
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y0 + y1) / 2))))
    res = 40075016.686 * math.cos(math.radians(lat)) / scale
    if mask.sum() < 4:
        # tiny place: use the cell under its centre and its neighbours
        cy, cx = int(((y0 + y1) / 2) * scale - oy), int(((x0 + x1) / 2) * scale - ox)
        mask[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2] = True
    mask[0, :] = mask[-1, :] = False
    mask[:, 0] = mask[:, -1] = False
    e = elev
    a, b, c = e[:-2, :-2], e[:-2, 1:-1], e[:-2, 2:]
    d, f = e[1:-1, :-2], e[1:-1, 2:]
    g, h, ii = e[2:, :-2], e[2:, 1:-1], e[2:, 2:]
    dzdx = ((c + 2 * f + ii) - (a + 2 * d + g)) / (8 * res)
    dzdy = ((g + 2 * h + ii) - (a + 2 * b + c)) / (8 * res)
    m = mask[1:-1, 1:-1] & np.isfinite(e[1:-1, 1:-1]) & (e[1:-1, 1:-1] > -500)
    els = e[1:-1, 1:-1][m]
    if els.size < 4:
        return None
    out = {"e": [round(float(v)) for v in (els.min(), els.mean(), els.max(), np.percentile(els, 10), np.percentile(els, 90))],
           "res": round(res, 1), "n": int(els.size)}
    if res <= 35:
        gx, gy = dzdx[m], dzdy[m]
        ok = np.isfinite(gx) & np.isfinite(gy)
        gx, gy = gx[ok], gy[ok]
        s = np.degrees(np.arctan(np.hypot(gx, gy)))
        if s.size:
            out["s"] = [round(float(s.mean()), 1), round(float(np.percentile(s, 90)), 1)]
            steep = s >= 2
            out["flat"] = round(float(1 - steep.mean()), 2)
            if steep.any():
                asp = (np.degrees(np.arctan2(-gx[steep], gy[steep])) + 360) % 360
                w = np.sin(np.radians(s[steep]))
                sx, sy = float((w * np.sin(np.radians(asp))).sum()), float((w * np.cos(np.radians(asp))).sum())
                R = math.hypot(sx, sy) / float(w.sum())
                sect = np.bincount(np.round(asp / 45).astype(int) % 8, minlength=8)
                out["dom"] = SECTORS[int(sect.argmax())]
                out["asp"] = round((math.degrees(math.atan2(sx, sy)) + 360) % 360) if R > 0.2 else None
    return out


_TILES = None


def work_one(r):
    global _TILES
    if _TILES is None:
        _TILES = Tiles()
    pid, bbox = r[1], r[6]
    try:
        polys = _TILES.outline(pid, bbox)
        t = measure(polys, r[3] == "vineyard") if polys else None
    except Exception as ex:  # one bad place must not stop the run
        print("fail", pid, ex, flush=True)
        t = None
    return pid, t


def work_chunk(chunk, threads):
    with ThreadPoolExecutor(threads) as ex:
        return list(ex.map(work_one, chunk))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="country code")
    ap.add_argument("--workers", type=int, default=8, help="threads per process (downloads)")
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 4)
    args = ap.parse_args()
    index = json.load(open(os.path.join(DATA, "search.json"), encoding="utf-8"))
    files = sorted(glob.glob(os.path.join(DATA, "details-*.json")))
    details = {f: json.load(open(f, encoding="utf-8")) for f in files}
    where = {pid: f for f, dd in details.items() for pid in dd}
    todo = [r for r in index if where.get(r[1]) and (not args.only or r[2] == args.only.upper())
            and details[where[r[1]]][r[1]].get("outline_quality") != "point" and r[6][0] != r[6][2]]
    print("places:", len(todo), flush=True)
    # neighbouring places share tiles: sort by position and hand out contiguous chunks
    todo.sort(key=lambda r: (r[1].split("-")[0], round((r[6][0] + r[6][2]) / 2, 1), round((r[6][1] + r[6][3]) / 2, 1)))
    chunks = [todo[i:i + 40] for i in range(0, len(todo), 40)]
    results = []
    with ProcessPoolExecutor(args.procs) as ex:
        for k, part in enumerate(ex.map(work_chunk, chunks, [args.workers] * len(chunks))):
            results += part
            if (k + 1) % 10 == 0:
                print(len(results), "/", len(todo), flush=True)
    got = 0
    for pid, t in results:
        d = details[where[pid]][pid]
        d.pop("terrain", None)
        if t:
            d["terrain"] = t
            got += 1
    for f, dd in details.items():
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(dd, fh, ensure_ascii=False, separators=(",", ":"))
    print("measured:", got, "of", len(todo))


if __name__ == "__main__":
    main()
