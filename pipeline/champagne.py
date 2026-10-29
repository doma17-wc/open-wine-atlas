"""Champagne in depth: the vineyard zones and every commune of the appellation with its cru rating.

Reads pipeline/lists/champagne.json (editorial, every figure with its source) and draws:
  - each commune of the Champagne AOC (French commune boundaries, gregoiredavid/france-geojson, from IGN ADMIN EXPRESS)
    with its rank on the old échelle des crus: grand cru (100 %), premier cru (90 to 99 %), the rest
  - each vineyard zone (Montagne de Reims, Vallée de la Marne, Côte des Blancs, Côte de Sézanne, Côte des Bar...)
    as the union of its communes
A commune is much larger than its vines, so the outlines are marked approximate (dashed); the planted vines come from
the vineyard layer of the map.

Runs on top of the published web/data, like ch_regions.py:
  build/champagne.geojsonl     the new places
  web/data/details-fr.json     their facts
  web/data/search.json         their search rows
  web/data/tree.json           zones under the Champagne AOC, communes under their zone
Then: python pipeline/merge_overview.py build/champagne.geojsonl --drop-src champ

Raw: raw/champagne/communes-<dept>.geojson (github.com/gregoiredavid/france-geojson), raw/champagne/code_map.json
     (AOC commune name -> INSEE code, checked against the EU PDO outline), raw/geonames/cities5000.json.
"""
import glob
import json
import math
import os

import shapely
from shapely.geometry import mapping, shape
from shapely.ops import polylabel

from ch_regions import extent_km, wineries_in
from common import BUILD, RAW, ROOT, round_geom, slug
from context import Towns, bearing, hav

WEB = os.path.join(ROOT, "web", "data")
LIST = os.path.join(ROOT, "pipeline", "lists", "champagne.json")
SRC = "champ"
AOC = "fr-eupdo-PDO-FR-A1359"
GROUP = "g:FR/champagne"
OUTLINE_SRC = {"name": "French commune boundaries (IGN ADMIN EXPRESS via france-geojson)", "licence": "Licence Ouverte 2.0",
               "source": "github.com/gregoiredavid/france-geojson"}


def zone_id(name):
    return "fr-champ-z-" + slug(name)


def ha_of(g):
    k = 111.32 * math.cos(math.radians(g.centroid.y)) * 110.57 * 100
    return round(g.area * k)


def centre(g):
    return polylabel(max(getattr(g, "geoms", [g]), key=lambda q: q.area), tolerance=0.0005)


def main():
    spec = json.load(open(LIST, encoding="utf-8"))
    codes = json.load(open(os.path.join(RAW, "champagne", "code_map.json"), encoding="utf-8"))
    geo = {}
    for f in glob.glob(os.path.join(RAW, "champagne", "communes-*.geojson")):
        for ft in json.load(open(f, encoding="utf-8"))["features"]:
            geo[ft["properties"]["code"]] = shapely.make_valid(shape(ft["geometry"]))
    pub = json.load(open(os.path.join(WEB, "details-fr.json"), encoding="utf-8"))
    aoc = pub[AOC]
    towns, cities = Towns(5000), Towns(30000)

    zones = spec["zones"]
    communes = spec["communes"]
    missing = set(codes) - set(communes)
    assert not missing, f"communes without data: {sorted(missing)}"
    extra = set(communes) - set(codes)
    assert not extra, f"communes without outline: {sorted(extra)}"
    for c, v in communes.items():
        assert v["zone"] in zones, f"{c}: unknown zone {v['zone']}"

    places = []  # (props, geometry, details)
    zgeom = {z: [] for z in zones}
    for name, v in communes.items():
        g = round_geom(geo[codes[name]].simplify(0.0002, preserve_topology=True), 5)
        zgeom[v["zone"]].append(geo[codes[name]])
        shown = v.get("display", name)
        rank = v.get("cru", "")
        typ = {"grand_cru": "Grand cru village", "premier_cru": "Premier cru village"}.get(rank, "Champagne village")
        d = {"type": typ, "zone": v["zone"], "official_name": name if shown != name else None,
             "category": "Quality Sparkling Wine, Wine", "grapes": aoc.get("grapes"),
             "communes": [shown], "insee": codes[name]}
        if v.get("pct"):
            d["echelle_pct"] = v["pct"]
        if v.get("echelle_note"):
            d["echelle_note"] = v["echelle_note"]
        if v.get("rules"):
            d["rules"] = v["rules"]
        if v.get("note"):
            d["atlas_note"] = v["note"]
        if v.get("refs"):
            d["refs"] = v["refs"]
        d["outline_quality"] = "approx"
        d["outline"] = "The commune of " + shown + ". Champagne is delimited commune by commune; the vines are only part of it, the vineyard layer of the map shows where they are."
        d["outline_area_ha"] = ha_of(g)
        d["outline_source"] = OUTLINE_SRC
        places.append(({"id": "fr-champ-" + codes[name], "name": shown, "country": "FR", "level": "subzone", "rank": rank,
                        "parent": v["zone"], "src": SRC, "ol": "approx"}, g, {k: x for k, x in d.items() if x is not None}))

    order = list(zones)
    for z in order:
        zv = zones[z]
        g = shapely.make_valid(shapely.union_all(zgeom[z]))
        g = round_geom(g.buffer(0.0003).buffer(-0.0003).simplify(0.0004, preserve_topology=True), 5)
        cs = [c for c, v in communes.items() if v["zone"] == z]
        d = {"type": "Vineyard zone", "wine_region": "Champagne", "deep_open": True, "grapes": aoc.get("grapes"),
             "category": "Quality Sparkling Wine, Wine",
             "communes": sorted(communes[c].get("display", c) for c in cs)}
        for k in ("vine_area_ha", "vine_area_src", "vine_area_note", "grape_share", "grape_share_note", "atlas_note", "refs", "rules"):
            if zv.get(k) is not None:
                d[k] = zv[k]
        gc = sum(communes[c].get("cru") == "grand_cru" for c in cs)
        pc = sum(communes[c].get("cru") == "premier_cru" for c in cs)
        d["note"] = f"{len(cs)} communes: {gc} grand cru, {pc} premier cru, {len(cs) - gc - pc} other villages."
        d["outline_quality"] = "approx"
        d["outline"] = "Union of the communes of the zone. The vines are only part of it: the vineyard layer of the map shows where they are."
        d["outline_area_ha"] = ha_of(g)
        d["outline_source"] = OUTLINE_SRC
        places.insert(order.index(z), ({"id": zone_id(z), "name": z, "country": "FR", "level": "subzone", "rank": "",
                                        "parent": "Champagne", "src": SRC, "ol": "approx", "lz": zv.get("label_zoom", 7)}, g, d))

    geoms = [g for _, g, _ in places]
    wins = wineries_in(geoms)
    feats, details = [], {}
    for i, (p, g, d) in enumerate(places):
        c = centre(g)
        d["lat"], d["lon"] = round(c.y, 5), round(c.x, 5)
        d["extent_km"] = extent_km(g)
        t = towns.nearest(d["lat"], d["lon"])
        if t:
            d["near_town"] = [t["name"], round(hav(t["latitude"], t["longitude"], d["lat"], d["lon"]), 1), bearing(t["latitude"], t["longitude"], d["lat"], d["lon"])]
        ct = cities.nearest(d["lat"], d["lon"], skip=t["name"] if t else None)
        if ct:
            d["near_city"] = [ct["name"], round(hav(ct["latitude"], ct["longitude"], d["lat"], d["lon"])), bearing(ct["latitude"], ct["longitude"], d["lat"], d["lon"]), ct["population"]]
        if i in wins:
            d["wineries_count"] = len(wins[i])
            d["wineries"] = wins[i][:40]
        feats.append({"type": "Feature", "properties": p, "geometry": mapping(g)})
        details[p["id"]] = d

    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "champagne.geojsonl"), "w", encoding="utf-8") as f:
        for ft in feats:
            f.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"  wrote {len(feats)} places -> build/champagne.geojsonl")

    # details-fr.json: replace the Champagne places, refresh the AOC record
    pub = {k: v for k, v in pub.items() if not k.startswith("fr-champ-")}
    for k, v in spec.get("aoc", {}).items():
        pub[AOC][k] = v
    pub.update(details)
    with open(os.path.join(WEB, "details-fr.json"), "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  details-fr.json: {len(pub)} records")

    # search.json
    from build_index import ORDER
    spath = os.path.join(WEB, "search.json")
    rows = [r for r in json.load(open(spath, encoding="utf-8")) if not str(r[1]).startswith("fr-champ-")]
    for ft in feats:
        p = ft["properties"]
        b = [round(x, 4) for x in shape(ft["geometry"]).bounds]
        d = details[p["id"]]
        alt = ", ".join(x for x in [d.get("official_name", "")] + [r.get("name", "") if isinstance(r, dict) else "" for r in []] if x)
        rows.append([p["name"], p["id"], "FR", p["level"], p["rank"], p["parent"], b, alt])
    rows.sort(key=lambda r: (ORDER.get(r[3], 4), r[0]))
    with open(spath, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  search.json: {len(rows)} places")

    # tree.json: Champagne AOC -> zones -> communes (grands crus, premiers crus, then the rest, by name)
    tpath = os.path.join(WEB, "tree.json")
    tree = json.load(open(tpath, encoding="utf-8"))
    nodes = tree["nodes"]
    for k in [k for k in nodes if k.startswith("fr-champ-")]:
        del nodes[k]
    nodes[AOC] = [None, "place", None, [zone_id(z) for z in order], 0]
    rk = {"grand_cru": 0, "premier_cru": 1}
    for z in order:
        ks = [ft["properties"] for ft in feats if ft["properties"]["parent"] == z and not ft["properties"]["id"].startswith("fr-champ-z-")]
        ks.sort(key=lambda p: (rk.get(p["rank"], 2), slug(p["name"])))
        nodes[zone_id(z)] = [None, "place", None, [p["id"] for p in ks], 0]

    def total(k):
        n = nodes.get(k)
        if not n:
            return 0
        s = 0
        for c in n[3]:
            s += (total(c) if c.startswith("g:") else 1 + total(c))
        n[4] = s
        return s
    allb = [shape(ft["geometry"]).bounds for ft in feats] + [nodes[GROUP][2]]
    nodes[GROUP][2] = [round(min(b[0] for b in allb), 4), round(min(b[1] for b in allb), 4), round(max(b[2] for b in allb), 4), round(max(b[3] for b in allb), 4)]
    # France keeps its own count (grands crus hang under more than one Burgundy village): add the difference only
    old = nodes[GROUP][4]
    total(GROUP)
    nodes["g:FR"][4] += nodes[GROUP][4] - old
    json.dump(tree, open(tpath, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"  tree.json: Champagne {nodes[GROUP][4]} places")


if __name__ == "__main__":
    main()
