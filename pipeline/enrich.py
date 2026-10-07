"""Enrich every place with facts computed from open data.

For each place (appellation, sub-zone, climat, Einzellage …):
  - position: label point (lat/lon), north-south and east-west extent, number of separate plots
  - bedrock: share of GLiM lithology classes under the place (Hartmann & Moosdorf 2012, CC BY 3.0)
  - wineries: OpenStreetMap wineries inside the outline (ODbL)
  - neighbours: adjoining climats / Einzellagen (vineyard level only)
  - share of parent: how much of its appellation or Großlage the place covers
  - wine rules: per-wine colour, category, main and secondary grapes, max yield, min density
    (France and Italy, from the per-wine PDO data derived from Candiago et al. 2022, CC BY 4.0)

Output: build/enrich.json  {id: {...}}
"""
import csv
import json
import math
import os
import random
from collections import Counter, defaultdict

import shapely
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform
from shapely.prepared import prep as prepare_geom
from shapely.strtree import STRtree

from common import BUILD, RAW, norm

random.seed(7)
TO_M = Transformer.from_crs(4326, 3035, always_xy=True).transform

GLIM = {
    "su": "Unconsolidated sediments", "ss": "Siliciclastic sedimentary rocks (sandstone, shale)",
    "sm": "Mixed sedimentary rocks", "sc": "Carbonate sedimentary rocks (limestone, marl, dolomite)",
    "py": "Pyroclastics", "ev": "Evaporites", "mt": "Metamorphic rocks (schist, slate, gneiss)",
    "pa": "Acid plutonic rocks (granite)", "pi": "Intermediate plutonic rocks", "pb": "Basic plutonic rocks",
    "va": "Acid volcanic rocks", "vi": "Intermediate volcanic rocks", "vb": "Basic volcanic rocks (basalt)",
    "ig": "Ice and glaciers", "wb": "Water bodies", "nd": "No data",
}


def read(name):
    path = os.path.join(BUILD, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def grand_cru_apps():
    """Real (parcel-level) geometry of grand cru appellations, streamed from the big file."""
    out = []
    with open(os.path.join(BUILD, "fr_appellations.geojsonl"), encoding="utf-8") as f:
        for line in f:
            if '"rank":"grand_cru"' in line:
                out.append(json.loads(line))
    return out


def sample_points(geom, n=60, tries=4000):
    minx, miny, maxx, maxy = geom.bounds
    prep = prepare_geom(geom)
    pts = []
    for _ in range(tries):
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if (prep.contains(p) if prep else geom.contains(p)):
            pts.append(p)
            if len(pts) >= n:
                break
    if not pts:
        pts = [geom.representative_point()]
    return pts


def main():
    places = (read("fr_overview.geojsonl") + read("fr_denominations.geojsonl") + read("eu_appellations.geojsonl")
              + read("ch_appellations.geojsonl") + read("de_einzellagen.geojsonl") + read("de_grosslagen.geojsonl"))
    gc = {ft["properties"]["id"]: ft for ft in grand_cru_apps()}
    geoms = {}
    for ft in places:
        pid = ft["properties"]["id"]
        geoms[pid] = shape(gc[pid]["geometry"]) if pid in gc else shape(ft["geometry"])
    props = {ft["properties"]["id"]: ft["properties"] for ft in places}
    print("places:", len(places))
    out = defaultdict(dict)

    # ---- position
    for pid, g in geoms.items():
        try:
            lp = shapely.polylabel(max(getattr(g, "geoms", [g]), key=lambda x: x.area), tolerance=0.00005)
        except Exception:
            lp = g.representative_point()
        minx, miny, maxx, maxy = g.bounds
        kx = 111.32 * math.cos(math.radians((miny + maxy) / 2))
        out[pid]["lat"], out[pid]["lon"] = round(lp.y, 5), round(lp.x, 5)
        out[pid]["extent_km"] = [round((maxy - miny) * 110.57, 2), round((maxx - minx) * kx, 2)]
        out[pid]["plots"] = len(getattr(g, "geoms", [g]))

    # ---- bedrock (GLiM)
    print("bedrock…")
    glim = json.load(open(os.path.join(RAW, "geo", "glim_west_europe.geojson"), encoding="utf-8"))
    polys, codes = [], []
    for ft in glim["features"]:
        g = shape(ft["geometry"])
        for part in getattr(g, "geoms", [g]):
            polys.append(part)
            codes.append(ft["properties"]["lithology_class"])
    tree = STRtree(polys)
    for pid, g in geoms.items():
        # the lithology map is coarse (1:3.75 M): for small places sample a ~1 km halo so that a narrow
        # strip on the edge of two map units does not read as 100% of one of them
        ext = out[pid]["extent_km"]
        pts = sample_points(g.buffer(0.012) if max(ext) < 2 else g)
        c = Counter()
        for p in pts:
            for i in tree.query(p):
                if polys[i].contains(p):
                    if codes[i] not in ("wb", "nd", "ig"):  # rivers, lakes, gaps are not bedrock
                        c[codes[i]] += 1
                    break
        tot = sum(c.values())
        if tot:
            out[pid]["bedrock"] = [[GLIM.get(k, k), round(100 * v / tot)] for k, v in c.most_common(3) if v / tot >= 0.1]

    # ---- wineries inside
    print("wineries…")
    wineries = read("osm_wineries.geojsonl")
    import re
    noise = re.compile(r"apartment|appartament|hotel|b&b|bed and breakfast|centro storico|museum|mus[eé]e|museo|camping|"
                       r"restaurant|ristorante|parking|parcheggio|chambre|gîte|gite|ferienwohnung|pension", re.I)
    wineries = [w for w in wineries if not noise.search(w["properties"]["name"])]
    wpts = [shape(w["geometry"]) for w in wineries]
    wtree = STRtree(wpts)
    for pid, g in geoms.items():
        if props[pid]["level"] == "region":
            continue
        hits = [i for i in wtree.query(g) if g.contains(wpts[i])]
        if hits:
            out[pid]["wineries_count"] = len(hits)
            out[pid]["wineries"] = [[wineries[i]["properties"]["name"], wineries[i]["properties"].get("web", "")]
                                    for i in sorted(hits, key=lambda i: wineries[i]["properties"]["name"])[:40]]

    # ---- neighbours (vineyard level: climats, grand cru appellations, Einzellagen)
    print("neighbours…")
    vids = [pid for pid in geoms if props[pid]["level"] == "vineyard" or pid in gc]
    vgeo = [transform(TO_M, geoms[pid]) for pid in vids]
    vtree = STRtree(vgeo)
    for i, pid in enumerate(vids):
        near = []
        buf = vgeo[i].buffer(12)
        for j in vtree.query(buf):
            if j == i or props[vids[j]]["name"] == props[pid]["name"]:
                continue
            if buf.intersects(vgeo[j]) and not vgeo[i].within(vgeo[j]) and not vgeo[j].within(vgeo[i]):
                near.append(vids[j])
        if near:
            out[pid]["neighbours"] = sorted(set(near), key=lambda x: props[x]["name"])[:14]

    # ---- share of parent (France climats in their appellation, German Lagen in their Großlage)
    print("shares…")
    fr_area = {}
    det = {}
    for name in ("fr_details.json", "de_details.json"):
        det.update(json.load(open(os.path.join(BUILD, name), encoding="utf-8")))
    for pid, d in det.items():
        if pid.startswith("fr-inao-a"):
            fr_area[props.get(pid, {}).get("name")] = d.get("area_ha")
    gl_area = {}
    for pid, p in props.items():
        if pid.startswith("de-rlp-gl-"):
            gl_area[(p["parent"], p["name"])] = transform(TO_M, geoms[pid]).area / 10000
    for pid, p in props.items():
        d = det.get(pid, {})
        if pid.startswith("fr-inao-d") and d.get("area_ha") and fr_area.get(p["parent"]):
            out[pid]["share_of_parent"] = round(100 * d["area_ha"] / fr_area[p["parent"]], 1)
        if pid.startswith("de-rlp-") and not pid.startswith("de-rlp-gl-") and d.get("grosslage"):
            ga = gl_area.get((d.get("region"), d["grosslage"]))
            if ga and d.get("area_ha"):
                out[pid]["share_of_grosslage"] = round(100 * d["area_ha"] / ga, 1)

    # ---- per-wine rules (France, Italy)
    print("wine rules…")
    rules = defaultdict(list)
    seen = set()
    with open(os.path.join(RAW, "pdowine", "PDO_wine_data_IT_FR.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            def num(v):
                v = (v or "").strip().replace(",", ".")
                return None if v in ("", "na") else v
            split = lambda v: [x.strip() for x in (v or "").split(";") if x.strip() and x.strip() != "na"]
            key = (r["PDOid"], r["WineNam"], r["Color"], r["Category"], r["Main_var"])
            if key in seen:
                continue
            seen.add(key)
            rules[r["PDOid"]].append({k: v for k, v in {
                "wine": r["WineNam"], "colour": r["Color"], "category": r["Category"],
                "main": split(r["Main_var"]), "secondary": split(r["Second_var"])[:30],
                "secondary_total": len(split(r["Second_var"])),
                "yield_hl": num(r["Max_yield_hl"]), "yield_kg": num(r["Max_yield_kg"]), "density": num(r["Min_density"]),
                "registered": (r["Registration"] or "")[:10]}.items() if v not in (None, "", [])})
            rules[("name", r["Country"], norm(r["PDOnam"]))] = r["PDOid"]
            for part in r["PDOnam"].split(" / "):
                rules[("name", r["Country"], norm(part))] = r["PDOid"]
    # EU id per French INAO appellation, matched by official name
    eu_ids = {}
    with open(os.path.join(RAW, "eupdo", "PDO_EU_id.csv"), encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            for part in r["PDOnam"].split(" / "):
                eu_ids[(r["Country"], norm(part))] = r
    matched = 0
    for pid, p in props.items():
        pdo = None
        if "-eupdo-" in pid:
            pdo = pid.split("-eupdo-")[1]
        elif pid.startswith("fr-inao-a"):
            official = det.get(pid, {}).get("official_name", p["name"])
            for part in official.split(" ou "):
                k = ("name", "FR", norm(part))
                if k in rules:
                    pdo = rules[k]
                    break
                if ("FR", norm(part)) in eu_ids:
                    pdo = eu_ids[("FR", norm(part))]["PDOid"]
                    break
            if pdo:
                matched += 1
                e = next((eu_ids[k] for k in eu_ids if eu_ids[k]["PDOid"] == pdo), None)
                if e:
                    out[pid].update({k: v for k, v in {
                        "registered": e["Registration"], "grapes": e["Varieties_OIV"],
                        "max_yield_hl_ha": e["Maximum_yield_hl"], "min_planting_density": e["Minimum_planting_density"],
                        "eu_register": e["PDOinfo"], "pdo_id": pdo}.items() if v and v != "na"})
        if pdo and rules.get(pdo):
            out[pid]["wines"] = rules[pdo]
    print("French appellations matched to EU rules:", matched)

    with open(os.path.join(BUILD, "enrich.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    n = Counter()
    for v in out.values():
        for k in v:
            n[k] += 1
    print("enriched:", len(out), dict(n))


if __name__ == "__main__":
    main()
