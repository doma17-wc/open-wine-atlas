"""Build the web data: vector tiles (PMTiles), label points, search index and place details.

Run after the source scripts (inao.py, eu_pdo.py, rlp.py, ch.py, osm.py).
Needs tippecanoe on PATH (https://github.com/felt/tippecanoe).

Output in web/data/:
  base.pmtiles          countries, lakes, rivers
  overview.pmtiles      every appellation outline + labels, zoom 4-10
  fr-<group>.pmtiles    France at parcel detail (appellations, premiers crus, climats), zoom 9-14
  de-rlp.pmtiles        German Einzellagen and Großlagen, zoom 8-14
  poi.pmtiles           wineries (all countries) and Swiss vineyard areas
  search.json           name index with bounding boxes
  details-<cc>.json     facts per place, loaded when a place is opened
  manifest.json         which tile file covers which area and zooms
"""
import json
import os
import subprocess
from collections import defaultdict

import shapely
from shapely.geometry import mapping, shape

from common import BUILD, ROOT, slug

WEB = os.path.join(ROOT, "web", "data")
TMP = os.path.join(BUILD, "tiles")
os.makedirs(WEB, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
TIPPECANOE = os.environ.get("TIPPECANOE", "tippecanoe")


def read(name):
    path = os.path.join(BUILD, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def area_ha(geom):
    # rough equal-area at mid latitudes is enough for zoom thresholds
    import math
    c = geom.centroid
    k = (111.32 * math.cos(math.radians(c.y))) * 110.57  # km2 per deg2
    return geom.area * k * 100


def label_minzoom(level, ha, country):
    if level == "region":
        return 5
    if level == "appellation":
        if ha > 150000: return 5
        if ha > 30000: return 6
        if ha > 6000: return 7
        if ha > 1500: return 8
        if ha > 300: return 9
        return 10
    if level == "subzone":
        return 10 if ha > 500 else 11
    if level == "vineyard":
        return 12 if country == "DE" else 13
    return 13


def write_geojsonl(path, feats):
    with open(path, "w", encoding="utf-8") as f:
        for ft in feats:
            f.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")


def tippecanoe(out, layers, minz, maxz, extra=()):
    args = [TIPPECANOE, "-o", out, "--force", f"-Z{minz}", f"-z{maxz}", "--no-tile-size-limit",
            "--no-feature-limit", "--detect-shared-borders", "--simplification=4", "-q"]
    for name, path in layers:
        args += ["-L", f"{name}:{path}"]
    subprocess.run(args + list(extra), check=True)
    print(f"  {os.path.basename(out)}: {os.path.getsize(out) / 1e6:.1f} MB")


def short_name(p):
    """Map label for a climat: drop the appellation prefix and the cru wording."""
    name, parent = p["name"], p.get("parent") or ""
    if p["level"] == "vineyard" and parent and name.startswith(parent + " "):
        rest = name[len(parent) + 1:]
        for pre in ("premier cru ", "grand cru "):
            if rest.startswith(pre):
                rest = rest[len(pre):]
        return rest or name
    return name


def labels_for(feats):
    out = []
    for ft in feats:
        p = ft["properties"]
        if not p.get("name"):
            continue
        g = shape(ft["geometry"])
        if g.is_empty:
            continue
        try:
            pt = shapely.polylabel(max(getattr(g, "geoms", [g]), key=lambda x: x.area), tolerance=0.0005)
        except Exception:
            pt = g.representative_point()
        ha = area_ha(g)
        q = dict(p)
        q["ha"] = round(ha)
        q["short"] = short_name(p)
        out.append({"type": "Feature", "properties": q, "geometry": mapping(pt),
                    "tippecanoe": {"minzoom": label_minzoom(p["level"], ha, p["country"])}})
    return out


def main():
    manifest = {"files": []}

    # ---------- base map
    base = os.path.join(WEB, "base.pmtiles")
    tippecanoe(base, [("countries", os.path.join(BUILD, "base", "countries.geojson")),
                      ("lakes", os.path.join(BUILD, "base", "lakes.geojson")),
                      ("rivers", os.path.join(BUILD, "base", "rivers.geojson"))], 0, 8,
               ["--drop-smallest-as-needed", "--simplification=2", "--detect-shared-borders"])
    manifest["files"].append({"file": "base.pmtiles", "minzoom": 0, "maxzoom": 8, "bounds": None})

    only_ov = os.environ.get("ONLY") == "overview"
    fr_ov = read("fr_overview.geojsonl")  # generalised outlines from fr_overview.py
    fr_apps = [] if only_ov else read("fr_appellations.geojsonl")
    fr_dens = [] if only_ov else read("fr_denominations.geojsonl")
    eu = read("eu_appellations.geojsonl")
    ch = read("ch_appellations.geojsonl")
    us = read("us_appellations.geojsonl")
    de_lagen = read("de_einzellagen.geojsonl")
    de_gross = read("de_grosslagen.geojsonl")
    osm_v = read("osm_vineyards.geojsonl")
    osm_w = read("osm_wineries.geojsonl")

    # ---------- overview: every appellation, generalised
    apps = fr_ov + eu + ch + us
    labels = labels_for(apps)
    # the overview only needs ~80 m precision: parcel detail comes from the regional files
    gen = []
    for ft in apps:
        g = shape(ft["geometry"]).simplify(0.0008, preserve_topology=True)
        if not g.is_empty:
            gen.append({"type": "Feature", "properties": ft["properties"], "geometry": mapping(g)})
    write_geojsonl(os.path.join(TMP, "apps.geojsonl"), gen)
    write_geojsonl(os.path.join(TMP, "labels.geojsonl"), labels)
    ov = os.path.join(WEB, "overview.pmtiles")
    tippecanoe(ov, [("appellations", os.path.join(TMP, "apps.geojsonl")),
                    ("labels", os.path.join(TMP, "labels.geojsonl"))], 2, 9,
               ["--coalesce-densest-as-needed", "--extend-zooms-if-still-dropping"])
    manifest["files"].append({"file": "overview.pmtiles", "minzoom": 2, "maxzoom": 9, "bounds": None})
    if os.environ.get("ONLY") == "overview":
        return

    # ---------- France detail, split by INAO office so every file stays small
    fr_details = json.load(open(os.path.join(BUILD, "fr_details.json"), encoding="utf-8"))
    office_of_app = {ft["properties"]["name"]: fr_details[ft["properties"]["id"]].get("inao_office", "x")
                     for ft in fr_apps}
    groups = defaultdict(list)
    for ft in fr_apps:
        groups[office_of_app[ft["properties"]["name"]]].append(ft)
    for ft in fr_dens:
        groups[office_of_app.get(ft["properties"]["parent"], "x")].append(ft)
    for office, feats in sorted(groups.items()):
        key = "fr-" + slug(office)
        apps_ = [f for f in feats if f["properties"]["level"] == "appellation"]
        dens_ = [f for f in feats if f["properties"]["level"] != "appellation"]
        for f in feats:
            f.pop("tippecanoe", None)
        write_geojsonl(os.path.join(TMP, key + "-a.geojsonl"), apps_)
        write_geojsonl(os.path.join(TMP, key + "-d.geojsonl"), dens_)
        write_geojsonl(os.path.join(TMP, key + "-l.geojsonl"), labels_for(apps_ + dens_))
        out = os.path.join(WEB, key + ".pmtiles")
        tippecanoe(out, [("appellations", os.path.join(TMP, key + "-a.geojsonl")),
                         ("crus", os.path.join(TMP, key + "-d.geojsonl")),
                         ("labels", os.path.join(TMP, key + "-l.geojsonl"))], 9, 14)
        b = shapely.union_all([shape(f["geometry"]).envelope for f in feats]).bounds
        manifest["files"].append({"file": key + ".pmtiles", "minzoom": 9, "maxzoom": 14,
                                  "bounds": [round(x, 4) for x in b], "label": office})

    # ---------- Germany (Rheinland-Pfalz Einzellagen)
    if de_lagen:
        write_geojsonl(os.path.join(TMP, "de-l.geojsonl"), labels_for(de_lagen + de_gross))
        write_geojsonl(os.path.join(TMP, "de-v.geojsonl"), de_lagen)
        write_geojsonl(os.path.join(TMP, "de-g.geojsonl"), de_gross)
        out = os.path.join(WEB, "de-rlp.pmtiles")
        tippecanoe(out, [("crus", os.path.join(TMP, "de-v.geojsonl")),
                         ("grosslagen", os.path.join(TMP, "de-g.geojsonl")),
                         ("labels", os.path.join(TMP, "de-l.geojsonl"))], 8, 14)
        b = shapely.union_all([shape(f["geometry"]).envelope for f in de_lagen]).bounds
        manifest["files"].append({"file": "de-rlp.pmtiles", "minzoom": 8, "maxzoom": 14,
                                  "bounds": [round(x, 4) for x in b], "label": "Rheinland-Pfalz"})

    # ---------- points of interest + Swiss vineyard areas
    write_geojsonl(os.path.join(TMP, "wineries.geojsonl"), osm_w)
    write_geojsonl(os.path.join(TMP, "vineyards.geojsonl"), osm_v)
    out = os.path.join(WEB, "poi.pmtiles")
    tippecanoe(out, [("wineries", os.path.join(TMP, "wineries.geojsonl")),
                     ("vineyard_areas", os.path.join(TMP, "vineyards.geojsonl"))], 7, 14, ["-r1"])
    manifest["files"].append({"file": "poi.pmtiles", "minzoom": 7, "maxzoom": 14, "bounds": None})

    # ---------- search index
    from build_index import build_index
    build_index()

    # ---------- details per country
    merged = defaultdict(dict)
    for name in ["fr_details.json", "eu_details.json", "de_details.json", "ch_details.json"]:
        path = os.path.join(BUILD, name)
        if os.path.exists(path):
            for k, v in json.load(open(path, encoding="utf-8")).items():
                merged[k[:2]][k] = v
    for cc, d in merged.items():
        json.dump(d, open(os.path.join(WEB, f"details-{cc}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    json.dump(manifest, open(os.path.join(WEB, "manifest.json"), "w"), indent=1)
    print("done:", [f["file"] for f in manifest["files"]])


if __name__ == "__main__":
    main()
