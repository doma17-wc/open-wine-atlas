"""Add the world layer (world.py) and the worldwide wineries (osm.py) to an existing web/data build,
without re-running the EU and US sources.

  overview.pmtiles   world outlines, markers and labels merged in (tile-join); older world features dropped first
  overview-lo.pmtiles  every place at zoom 0-1 for the whole-world view, made from overview.pmtiles
  poi.pmtiles        rebuilt from osm.py (wineries in 44 countries, Swiss vineyard areas)
  search.json        world rows replaced
  details-<cc>.json  written for every world country, with OSM wineries inside each outline and editorial notes

A full rebuild (build_tiles.py, build_details.py) produces the same result from scratch.
Needs tippecanoe and tile-join on PATH.
Run: python pipeline/fetch_world.py && python pipeline/world.py && python pipeline/osm.py && python pipeline/build_world_web.py
"""
import json
import os
import re
import shutil
import subprocess
from collections import defaultdict

import shapely
from shapely import STRtree
from shapely.geometry import mapping, shape

from build_index import index_row, world_alt
from build_tiles import TMP, WEB, labels_for, tippecanoe, write_geojsonl
from common import BUILD, norm

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD_SRC = ["geob", "wa", "wao", "marker"]
TILE_JOIN = os.environ.get("TILE_JOIN", "tile-join")
ORDER = {"region": 0, "appellation": 1, "subzone": 2, "vineyard": 3}


def read(name):
    with open(os.path.join(BUILD, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def overview(world):
    gen = []
    for ft in world:
        g = shape(ft["geometry"])
        if g.geom_type != "Point":
            g = g.simplify(0.0008, preserve_topology=True)
        gen.append({"type": "Feature", "properties": ft["properties"], "geometry": mapping(g)})
    write_geojsonl(os.path.join(TMP, "world-apps.geojsonl"), gen)
    write_geojsonl(os.path.join(TMP, "world-labels.geojsonl"), labels_for(world))
    wpm = os.path.join(TMP, "world.pmtiles")
    tippecanoe(wpm, [("appellations", os.path.join(TMP, "world-apps.geojsonl")),
                     ("labels", os.path.join(TMP, "world-labels.geojsonl"))], 2, 9,
               ["--coalesce-densest-as-needed", "--extend-zooms-if-still-dropping"])
    ov = os.path.join(WEB, "overview.pmtiles")
    base = os.path.join(TMP, "overview-base.pmtiles")
    keep = json.dumps({"*": ["!in", "src"] + WORLD_SRC})
    subprocess.run([TILE_JOIN, "-q", "-f", "-pk", "-o", base, "-j", keep, ov], check=True)
    out = os.path.join(TMP, "overview-new.pmtiles")
    subprocess.run([TILE_JOIN, "-q", "-f", "-pk", "-o", out, base, wpm], check=True)
    shutil.move(out, ov)
    print(f"  overview.pmtiles: {os.path.getsize(ov) / 1e6:.1f} MB")


def overview_low():
    """overview-lo.pmtiles: every outline and marker at zoom 0-1, for the whole-world view.
    Made from the zoom 2 tiles of overview.pmtiles, so it needs no source data."""
    from collections import defaultdict as dd
    ov = os.path.join(WEB, "overview.pmtiles")
    parts, props = dd(list), {}
    for x in range(4):
        for y in range(4):
            r = subprocess.run(["tippecanoe-decode", ov, "2", str(x), str(y)], capture_output=True, text=True)
            if r.returncode or not r.stdout.strip():
                continue
            for layer in json.loads(r.stdout).get("features", []):
                if layer["properties"]["layer"] != "appellations":
                    continue
                for f in layer["features"]:
                    p = f["properties"]
                    props[p["id"]] = {k: p.get(k, "") for k in ("id", "name", "country", "level", "rank", "src", "ol")}
                    parts[p["id"]].append(shape(f["geometry"]))
    feats = []
    for pid, gs in parts.items():
        g = gs[0] if gs[0].geom_type == "Point" else shapely.union_all(gs).simplify(0.02, preserve_topology=True)
        if not g.is_empty:
            feats.append({"type": "Feature", "properties": props[pid], "geometry": mapping(g)})
    write_geojsonl(os.path.join(TMP, "lo.geojsonl"), feats)
    tippecanoe(os.path.join(WEB, "overview-lo.pmtiles"), [("appellations", os.path.join(TMP, "lo.geojsonl"))], 0, 1,
               ["--drop-smallest-as-needed"])


def poi():
    out = os.path.join(WEB, "poi.pmtiles")
    tippecanoe(out, [("wineries", os.path.join(BUILD, "osm_wineries.geojsonl")),
                     ("vineyard_areas", os.path.join(BUILD, "osm_vineyards.geojsonl"))], 7, 14, ["-r1"])


def search(world, details):
    path = os.path.join(WEB, "search.json")
    index = [r for r in json.load(open(path, encoding="utf-8")) if "-world-" not in r[1]]
    index += [index_row(ft, world_alt(ft["properties"], details.get(ft["properties"]["id"], {}))) for ft in world]
    index.sort(key=lambda r: (ORDER.get(r[3], 4), r[0]))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  search.json: {len(index)} places")
    return index


def wineries_inside(world, details):
    noise = re.compile(r"apartment|appartament|hotel|b&b|bed and breakfast|centro storico|museum|mus[eé]e|museo|camping|"
                       r"restaurant|ristorante|parking|parcheggio|chambre|gîte|gite|ferienwohnung|pension|lodge|guest ?house", re.I)
    ws = [w for w in read("osm_wineries.geojsonl") if not noise.search(w["properties"]["name"])]
    pts = [shape(w["geometry"]) for w in ws]
    tree = STRtree(pts)
    n = 0
    for ft in world:
        p = ft["properties"]
        g = shape(ft["geometry"])
        if g.geom_type == "Point" or p["level"] == "region":
            continue
        hits = [i for i in tree.query(g) if g.contains(pts[i])]
        if hits:
            d = details[p["id"]]
            d["wineries_count"] = len(hits)
            d["wineries"] = [[ws[i]["properties"]["name"], ws[i]["properties"].get("web", "")]
                             for i in sorted(hits, key=lambda i: ws[i]["properties"]["name"])[:40]]
            n += 1
    print(f"  wineries matched inside {n} world outlines")


def notes(index, details):
    by_name = defaultdict(list)
    for r in index:
        by_name[(r[2], norm(r[0]))].append(r)
    data = json.load(open(os.path.join(HERE, "notes", "editorial.json"), encoding="utf-8"))["notes"]
    hit = 0
    for n in data:
        pid = n.get("id")
        if not pid:
            cands = sorted(by_name.get((n["country"], norm(n["name"])), []), key=lambda r: ORDER.get(r[3], 9))
            pid = cands[0][1] if cands else None
        if pid in details:
            details[pid]["atlas_note"] = n["note"]
            hit += 1
    print(f"  editorial notes on world places: {hit}")


def main():
    world = read("world_appellations.geojsonl")
    details = json.load(open(os.path.join(BUILD, "world_details.json"), encoding="utf-8"))
    overview(world)
    overview_low()
    poi()
    index = search(world, details)
    wineries_inside(world, details)
    notes(index, details)
    by_cc = defaultdict(dict)
    for k, v in details.items():
        by_cc[k[:2]][k] = v
    for cc, d in by_cc.items():
        path = os.path.join(WEB, f"details-{cc}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    print("  details:", {cc: len(d) for cc, d in sorted(by_cc.items())})


if __name__ == "__main__":
    main()
