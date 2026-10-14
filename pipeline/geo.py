"""Geography layer: named rivers, lakes, mountain peaks, mountain ranges and towns.

Input (not committed, see sources.json):
  raw/ne/ne_10m_rivers_lake_centerlines, ne_10m_rivers_europe, ne_10m_rivers_north_america   (Natural Earth, public domain)
  raw/ne/ne_10m_lakes, ne_10m_lakes_europe, ne_10m_lakes_north_america
  raw/ne/ne_10m_geography_regions_elevation_points    peaks with their elevation
  raw/ne/ne_10m_geography_regions_polys               mountain ranges, plateaus, valleys
  raw/geonames/cities5000.json                        GeoNames towns of 5,000 people or more (CC BY 4.0)

Output:
  web/data/geo.pmtiles   layers rivers, river_labels, lakes, lake_labels, peaks, ranges, range_labels, towns (zoom 2-8, drawn deeper by overzoom)
  web/data/geo.json      search index: [name, kind, gid, [w, s, e, n], elevation or null, (other names)]

Every river, lake, peak and range carries a stable "gid" ("river:rhone", "lake:lake-geneva", "peak:mont-blanc").
The map highlights one by filtering on it, and #river:rhone in a link opens the map on it. A name used by
rivers far apart (the Main in Germany and in Ireland) gets one gid per stretch: "river:main", "river:main-2".

Names are the English Natural Earth names, like the rivers and lakes on the place sheets (pipeline/context.py).

Run:  python pipeline/geo.py        Needs tippecanoe on PATH and shapely.
"""
import json
import math
import os
import re
import shutil
import subprocess
import tempfile

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from common import RAW, ROOT, slug

DATA = os.path.join(ROOT, "web", "data")
NE = os.path.join(RAW, "ne")
TIPPECANOE = os.environ.get("TIPPECANOE", "tippecanoe")
DISTRICT = re.compile(r"\d|^(Circo|Municipio|Arrondissement|Stadtbezirk|Bezirk|Distrito|District|Quartiere|Ortsbezirk)|\s[IVXLC]+$", re.I)


def load(name):
    path = os.path.join(NE, name + ".geojson")
    if not os.path.exists(path):
        print("  missing", path)
        return []
    return json.load(open(path, encoding="utf-8"))["features"]


def prop(p, *keys):
    """Natural Earth spells its fields in lower case in some files and upper case in others."""
    for k in keys:
        for kk in (k, k.upper()):
            v = p.get(kk)
            if v not in (None, ""):
                return v
    return None


# typos in Natural Earth: letters lost to an old encoding
NAME_FIX = {"Sane": "Saône", "Galdhpiggen": "Galdhøpiggen", "Hvannadalshnkur": "Hvannadalshnúkur", "Jabal al Uwaynt": "Jabal al Uwaynat"}


def clean(name):
    name = re.sub(r"\s+", " ", str(name or "")).strip()
    name = NAME_FIX.get(name, name)
    # "ALPS" -> "Alps", "CAUCASUS MTS." -> "Caucasus Mountains"
    if name.isupper() and len(name) > 3:
        name = " ".join(w if w in ("de", "du", "la") else w.capitalize() for w in name.lower().split())
    name = re.sub(r"\bMts\.?$", "Mountains", name)
    name = re.sub(r"\bMt\.\s", "Mount ", name)
    return name


# one river, one name: Natural Earth names some stretches in English and others in the local language
RIVER_ALIAS = {"Rhein": "Rhine", "Rhin": "Rhine", "Tajo": "Tagus", "Tejo": "Tagus", "Drau": "Drava", "Maas": "Meuse", "Labe": "Elbe",
               "Odra": "Oder", "Donau": "Danube", "Dunaj": "Danube", "Duna": "Danube", "Dunav": "Danube", "Dunărea": "Danube"}
# other names people search for, and that OpenStreetMap uses along the way (Moselle in France, Douro in Portugal)
RIVER_ALTS = {"Mosel": ["Moselle"], "Duero": ["Douro"], "Rhine": ["Rhin", "Rijn"], "Tagus": ["Tejo", "Tajo"], "Danube": ["Donau", "Duna", "Dunărea", "Dunav"],
              "Saar": ["Sarre"], "Minho": ["Miño"], "Meuse": ["Maas"], "Elbe": ["Labe"], "Drava": ["Drau"], "Mur": ["Mura"], "Ticino": ["Tessin"],
              "Tiber": ["Tevere"], "Rhône": ["Rhone", "Rotten"], "Saône": ["Saone"], "Guadiana": [], "Inn": ["En"], "Oder": ["Odra"]}
LAKE_WORD = re.compile(r"lake|lac\b|lago|laguna|lagoa|see\b|see$|meer|loch|lough|reservoir|réservoir|embalse|albufeira|barrage|"
                       r"\bdam\b|lagoon|\bsea\b|pond|jezero|ozero|\bgöl|\bkul\b|\bnuur|\btó\b|\bvatn|järvi|sjön|\bjärv", re.I)


def lake_name(p):
    """"Geneva" -> "Lake Geneva": Natural Earth's English names drop the word lake that its main names keep."""
    en, name = clean(prop(p, "name_en")), clean(prop(p, "name"))
    if not en:
        return name, []
    # an English main name is kept as written: Seneca Lake, Okanagan Lake, Lake Geneva
    if re.search(r"\bLake\b", name or ""):
        return name, sorted({x for x in (en,) if x and x != name})
    if LAKE_WORD.search(en):
        return en, ([name] if name and name != en else [])
    full = "Lake " + en
    return full, sorted({x for x in (en, name) if x and x != full})


def rnd(b):
    return [round(b[0], 3), round(b[1], 3), round(b[2], 3), round(b[3], 3)]


def clusters(items, gap_deg):
    """Group (geometry, ...) items whose boxes lie within gap_deg of each other (union-find on boxes)."""
    boxes = [it[0].bounds for it in items]
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = boxes[i], boxes[j]
            if a[0] - gap_deg <= b[2] and b[0] - gap_deg <= a[2] and a[1] - gap_deg <= b[3] and b[1] - gap_deg <= a[3]:
                parent[find(i)] = find(j)
    out = {}
    for i in range(len(items)):
        out.setdefault(find(i), []).append(items[i])
    return list(out.values())


def assign_ids(kind, groups):
    """groups: {name: [items]} -> list of (gid, name, items) with one gid per separate stretch, largest first."""
    out = []
    used = set()
    for name, items in groups.items():
        parts = clusters(items, 1.0) if len(items) > 1 else [items]
        parts.sort(key=lambda its: -sum(it[0].length if it[0].geom_type.endswith("String") else it[0].area * 100 for it in its))
        for k, its in enumerate(parts):
            gid = kind + ":" + slug(name)
            if k or gid in used:
                n = 2
                while gid + "-" + str(n) in used:
                    n += 1
                gid = gid + "-" + str(n)
            used.add(gid)
            out.append((gid, name, its))
    return out


def chaikin(coords, rounds=1):
    """Round the corners of a line, so a label can follow it (Natural Earth lines zigzag at street scale)."""
    for _ in range(rounds):
        if len(coords) < 3:
            return coords
        out = [coords[0]]
        for (x0, y0), (x1, y1) in zip(coords, coords[1:]):
            out += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        out.append(coords[-1])
        coords = out
    return coords


def label_lines(geoms):
    """One smooth line per stretch of river, only for its name."""
    from shapely.geometry import LineString, MultiLineString
    from shapely.ops import linemerge
    parts = []
    for g in geoms:
        parts += list(getattr(g, "geoms", [g]))
    merged = linemerge(parts) if len(parts) > 1 else parts[0]
    out = []
    for ln in getattr(merged, "geoms", [merged]):
        ln = ln.simplify(0.004, preserve_topology=False)
        if ln.length < 0.02:
            continue
        out.append(LineString(chaikin(list(ln.coords))))
    return MultiLineString(out) if len(out) > 1 else (out[0] if out else None)


def tminz(z, lo=2, hi=8):
    return int(max(lo, min(hi, math.floor(z))))


def rivers():
    groups, unnamed = {}, []
    for f in ("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_europe", "ne_10m_rivers_north_america"):
        for ft in load(f):
            p, g = ft["properties"], ft.get("geometry")
            if not g:
                continue
            cla = str(prop(p, "featurecla") or "")
            if "Lake Centerline" in cla or "Canal" in cla:
                continue  # lines drawn across lakes, and canals
            geom = shape(g)
            if geom.is_empty:
                continue
            sr = prop(p, "scalerank")
            sr = int(sr) if sr is not None else 12
            mz = prop(p, "min_zoom")
            mz = float(mz) if mz is not None else 7
            raw = clean(prop(p, "name_en", "name"))
            name = RIVER_ALIAS.get(raw, raw)
            item = (geom, sr, mz, "intermittent" in cla.lower(), raw)
            if name:
                groups.setdefault(name, []).append(item)
            else:
                unnamed.append(item)
    feats, labels, index = [], [], []
    for gid, name, its in assign_ids("river", groups):
        box = unary_union([it[0] for it in its]).bounds
        sr = min(it[1] for it in its)
        alts = sorted({it[4] for it in its if it[4] != name} | set(RIVER_ALTS.get(name, [])))
        index.append([name, "river", gid, rnd(box), None, alts])
        lab = label_lines([it[0] for it in its])
        if lab is not None:
            labels.append({"type": "Feature", "properties": {"name": name, "gid": gid, "sr": sr}, "geometry": mapping(lab),
                           "tippecanoe": {"minzoom": tminz(min(it[2] for it in its) - 0.5, lo=4)}})
        for geom, s, mz, inter, _ in its:
            feats.append({"type": "Feature", "properties": {"name": name, "gid": gid, "sr": s, **({"int": 1} if inter else {})},
                          "geometry": mapping(geom), "tippecanoe": {"minzoom": tminz(mz - 1)}})
    for geom, s, mz, inter, _ in unnamed:
        feats.append({"type": "Feature", "properties": {"sr": s, **({"int": 1} if inter else {})}, "geometry": mapping(geom),
                      "tippecanoe": {"minzoom": tminz(mz - 1, lo=5)}})
    print("  rivers", len(feats), "named stretches", len(index), "label lines", len(labels))
    return feats, labels, index


def lakes():
    groups, unnamed = {}, []
    for f in ("ne_10m_lakes", "ne_10m_lakes_europe", "ne_10m_lakes_north_america"):
        for ft in load(f):
            p, g = ft["properties"], ft.get("geometry")
            if not g:
                continue
            geom = shape(g)
            if geom.is_empty:
                continue
            geom = geom.buffer(0) if not geom.is_valid else geom
            mz = prop(p, "min_zoom")
            ml = prop(p, "min_label")
            mz = float(mz) if mz is not None else 7
            ml = float(ml) if ml is not None else mz + 1
            name, alts = lake_name(p)
            item = (geom, mz, ml, alts)
            if name:
                groups.setdefault(name, []).append(item)
            else:
                unnamed.append(item)
    feats, labels, index = [], [], []
    for gid, name, its in assign_ids("lake", groups):
        # Natural Earth has big lakes twice: a rough world outline and a finer one in the Europe or North America file.
        # Keep the most detailed shape of each lake.
        geoms, seen = [], []
        nverts = lambda g: sum(len(p.exterior.coords) for p in getattr(g, "geoms", [g]) if hasattr(p, "exterior"))
        for it in sorted(its, key=lambda it: -nverts(it[0])):
            g = it[0]
            if any(g.intersects(s) and g.intersection(s).area > 0.3 * min(g.area, s.area) for s in seen):
                continue
            seen.append(g)
            geoms.append(it)
        whole = unary_union([it[0] for it in geoms])
        biggest = max((g for g in getattr(whole, "geoms", [whole])), key=lambda g: g.area)
        pt = biggest.representative_point()
        ml = min(it[2] for it in geoms)
        alts = sorted({a for it in its for a in it[3]})
        index.append([name, "lake", gid, rnd(whole.bounds), None, alts])
        labels.append({"type": "Feature", "properties": {"name": name, "gid": gid, "a": round(whole.area, 5)},
                       "geometry": mapping(pt), "tippecanoe": {"minzoom": tminz(ml - 1, lo=3)}})
        for geom, mz, _, _ in geoms:
            feats.append({"type": "Feature", "properties": {"name": name, "gid": gid}, "geometry": mapping(geom),
                          "tippecanoe": {"minzoom": tminz(mz - 1)}})
    for geom, mz, _, _ in unnamed:
        feats.append({"type": "Feature", "properties": {}, "geometry": mapping(geom), "tippecanoe": {"minzoom": tminz(mz - 1, lo=5)}})
    print("  lakes", len(feats), "named", len(index))
    return feats, labels, index


def peaks():
    groups = {}
    for ft in load("ne_10m_geography_regions_elevation_points"):
        p, g = ft["properties"], ft.get("geometry")
        cla = str(prop(p, "featurecla") or "").lower()
        ele = prop(p, "elevation")
        name = clean(prop(p, "name_en", "name"))
        if not g or not name or cla not in ("mountain", "volcano") or not ele or ele <= 0:
            continue
        mz = prop(p, "min_zoom")
        groups.setdefault(name, []).append((shape(g), int(ele), float(mz) if mz is not None else 7, cla))
    feats, index = [], []
    for gid, name, its in assign_ids("peak", groups):
        geom, ele, mz, cla = max(its, key=lambda it: it[1])
        x, y = geom.x, geom.y
        index.append([name, "peak", gid, rnd((x, y, x, y)), ele, []])
        feats.append({"type": "Feature", "properties": {"name": name, "gid": gid, "ele": ele, **({"v": 1} if cla == "volcano" else {})},
                      "geometry": mapping(geom), "tippecanoe": {"minzoom": tminz(mz - 1.5, lo=4)}})
    print("  peaks", len(feats))
    return feats, index


def prop_name_short(its):
    """The plain Natural Earth name of a range ("Vosges" for the Vosges Mountains), kept for search."""
    return its[0][3]


RANGE_CLASSES = {"Range/mtn": "range", "Plateau": "plateau", "Valley": "valley", "Foothills": "range"}


def ranges():
    groups = {}
    for ft in load("ne_10m_geography_regions_polys"):
        p, g = ft["properties"], ft.get("geometry")
        cla = RANGE_CLASSES.get(prop(p, "featurecla") or "")
        name = clean(prop(p, "name_en", "name"))
        if not g or not cla or not name:
            continue
        geom = shape(g)
        geom = geom.buffer(0) if not geom.is_valid else geom
        sr = prop(p, "scalerank")
        groups.setdefault(name, []).append((geom, int(sr) if sr is not None else 6, cla, clean(prop(p, "name"))))
    feats, labels, index = [], [], []
    for gid, name, its in assign_ids("range", groups):
        whole = unary_union([it[0] for it in its])
        sr = min(it[1] for it in its)
        cla = its[0][2]
        biggest = max((g for g in getattr(whole, "geoms", [whole])), key=lambda g: g.area)
        pt = biggest.representative_point()
        short = clean(prop_name_short(its))
        index.append([name, cla, gid, rnd(whole.bounds), None, [short] if short and short != name else []])
        labels.append({"type": "Feature", "properties": {"name": name, "gid": gid, "sr": sr, "k": cla},
                       "geometry": mapping(pt), "tippecanoe": {"minzoom": tminz(sr + 1, lo=2, hi=7)}})
        feats.append({"type": "Feature", "properties": {"name": name, "gid": gid, "k": cla},
                      "geometry": mapping(whole.simplify(0.02, preserve_topology=True)), "tippecanoe": {"minzoom": 2}})
    print("  ranges", len(feats))
    return feats, labels, index


def towns():
    path = os.path.join(RAW, "geonames", "cities5000.json")
    d = json.load(open(path, encoding="utf-8"))
    feats = []
    for v in d.values():
        pop = v.get("population") or 0
        if pop < 5000 or DISTRICT.search(v["name"]):
            continue
        name = {"Sitten": "Sion", "Siders": "Sierre"}.get(v["name"], v["name"])
        if name == "Freiburg" and v.get("countrycode") == "CH":
            name = "Fribourg"
        # the archive stops at zoom 8; the map shows towns under 25,000 people only from zoom 9.5 (a layer filter)
        z = 3 if pop >= 3_000_000 else 4 if pop >= 1_000_000 else 5 if pop >= 400_000 else 6 if pop >= 150_000 else \
            7 if pop >= 60_000 else 8
        feats.append({"type": "Feature", "properties": {"name": name, "pop": pop},
                      "geometry": {"type": "Point", "coordinates": [round(v["longitude"], 5), round(v["latitude"], 5)]},
                      "tippecanoe": {"minzoom": z}})
    print("  towns", len(feats))
    return feats


def write_l(path, feats):
    with open(path, "w", encoding="utf-8") as f:
        for ft in feats:
            f.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")


def main():
    if not shutil.which(TIPPECANOE):
        raise SystemExit("tippecanoe not found (https://github.com/felt/tippecanoe)")
    riv, riv_lab, riv_i = rivers()
    lk, lk_lab, lk_i = lakes()
    pk, pk_i = peaks()
    rg, rg_lab, rg_i = ranges()
    tw = towns()
    tmp = tempfile.mkdtemp(prefix="owa-geo-")
    layers = {"rivers": riv, "river_labels": riv_lab, "lakes": lk, "lake_labels": lk_lab, "peaks": pk, "ranges": rg, "range_labels": rg_lab, "towns": tw}
    args = [TIPPECANOE, "-o", os.path.join(DATA, "geo.pmtiles"), "--force", "-Z2", "-z8", "-r1",
            "--no-feature-limit", "--simplification=4", "--drop-smallest-as-needed", "--extend-zooms-if-still-dropping",
            "--attribution", "Natural Earth (public domain); GeoNames (CC BY 4.0)", "-n", "Open Wine Atlas geography", "-q"]
    for name, feats in layers.items():
        p = os.path.join(tmp, name + ".geojsonl")
        write_l(p, feats)
        args += ["-L", name + ":" + p]
    subprocess.run(args, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("  geo.pmtiles", os.path.getsize(os.path.join(DATA, "geo.pmtiles")))
    # search index: big things first so "Rhône" finds the river before a brook of the same name
    order = {"river": 0, "lake": 1, "range": 2, "plateau": 2, "valley": 2, "peak": 3}
    index = sorted(riv_i + lk_i + rg_i + pk_i, key=lambda r: (order[r[1]], r[0]))
    with open(os.path.join(DATA, "geo.json"), "w", encoding="utf-8") as f:
        json.dump([r[:5] + ([r[5]] if r[5] else []) for r in index], f, ensure_ascii=False, separators=(",", ":"))
    print("  geo.json", len(index), os.path.getsize(os.path.join(DATA, "geo.json")))


if __name__ == "__main__":
    main()
