"""Piemonte and Toscana in depth: the appellations by area, the cru communes of Barolo, Barbaresco and Roero with their
MGA, the sub-zones of Chianti, the UGA of Chianti Classico and the Pievi of Vino Nobile di Montepulciano.

Reads pipeline/lists/it_deep.json (editorial, every figure with its source) and:
  - groups the appellations of each region (Langhe and Roero, Asti and Monferrato, Alto Piemonte...; Chianti and central
    Tuscany, the coast...), the wide umbrella DOCs under "Regional appellations"
  - adds hectares, years of recognition, rules, notes and MGA lists to the appellation records
  - draws each commune of Barolo, Barbaresco and Roero (ISTAT boundaries) with its MGA, each Chianti sub-zone and each
    Chianti Classico UGA that follows whole communes as the union of its communes; the UGA that cover parts of communes
    and the Pievi of Montepulciano are markers on the village they are named after
  - redraws Chianti Classico on its nine communes (the EU inventory gives it the 76 communes of Chianti) and the
    appellations whose rank changed (for example Terre Alfieri, DOCG since 2020) on their listed communes
A commune is much larger than its vines, so the outlines are marked approximate (dashed); the planted vines come from
the vineyard layer of the map.

Runs on top of the published web/data, like champagne.py:
  build/it_deep.geojsonl       the new and redrawn places
  web/data/details-it.json     their facts
  web/data/search.json         their search rows
  web/data/tree.json           groups under each region, communes and sub-zones under their appellation
Then: python pipeline/merge_overview.py build/it_deep.geojsonl --drop-src itdeep

Raw: raw/it/limits_R_1_municipalities.geojson and limits_R_9_municipalities.geojson (github.com/openpolis/geojson-italy,
     ISTAT boundaries, CC BY 4.0), raw/geonames/cities5000.json.
"""
import json
import math
import os

import shapely
from shapely.geometry import Point, mapping, shape
from shapely.ops import polylabel

from ch_regions import extent_km, wineries_in
from common import BUILD, RAW, ROOT, norm, round_geom, slug
from context import Towns, bearing, hav

WEB = os.path.join(ROOT, "web", "data")
LIST = os.path.join(ROOT, "pipeline", "lists", "it_deep.json")
SRC = "itdeep"
PFX = "it-deep-"
REGION_CODE = {"piemonte": 1, "toscana": 9}
OUTLINE_SRC = {"name": "ISTAT municipal boundaries (via openpolis/geojson-italy)", "licence": "CC BY 4.0",
               "source": "github.com/openpolis/geojson-italy"}
COMMUNE_OUTLINE = ("The commune boundary: {app} is delimited commune by commune. The vines are only part of it: "
                   "the vineyard layer of the map shows where they are.")
PARTIAL_OUTLINE = ("The whole commune is drawn, but only part of it is inside {app}. The vineyard layer of the map shows "
                   "where the vines are.")
UNION_OUTLINE = ("Union of the communes of the {kind}{partial}. The vines are only part of it: the vineyard layer of the "
                 "map shows where they are.")
POINT_OUTLINE = "Location of the village the {kind} is named after. The {kind} covers the hills around it; its limits are not drawn."


def ha_of(g):
    k = 111.32 * math.cos(math.radians(g.centroid.y)) * 110.57 * 100
    return round(g.area * k)


def centre(g):
    if g.geom_type == "Point":
        return g
    return polylabel(max(getattr(g, "geoms", [g]), key=lambda q: q.area), tolerance=0.0005)


def bbox(g):
    return [round(x, 4) for x in g.bounds]


class Communes:
    """ISTAT municipalities of a region by name (and the old names of merged communes)."""

    def __init__(self, aliases):
        self.geo, self.name = {}, {}
        for code in REGION_CODE.values():
            path = os.path.join(RAW, "it", f"limits_R_{code}_municipalities.geojson")
            for ft in json.load(open(path, encoding="utf-8"))["features"]:
                p = ft["properties"]
                k = norm(p["name"])
                self.geo[k] = shapely.make_valid(shape(ft["geometry"]))
                self.name[k] = p["name"]
        self.alias = {norm(a): norm(b) for a, b in aliases.items()}

    def key(self, n):
        k = norm(n)
        k = self.alias.get(k, k)
        return k if k in self.geo else None

    def get(self, n):
        k = self.key(n)
        assert k, f"commune not in ISTAT boundaries: {n}"
        return self.geo[k]

    def union(self, names):
        g = shapely.make_valid(shapely.union_all([self.get(n) for n in names]))
        return g.buffer(0.0003).buffer(-0.0003)


def main():
    spec = json.load(open(LIST, encoding="utf-8"))
    com = Communes(spec.get("commune_alias", {}))
    pub = json.load(open(os.path.join(WEB, "details-it.json"), encoding="utf-8"))
    spath, tpath = os.path.join(WEB, "search.json"), os.path.join(WEB, "tree.json")
    rows = [r for r in json.load(open(spath, encoding="utf-8")) if not str(r[1]).startswith(PFX)]
    tree = json.load(open(tpath, encoding="utf-8"))
    nodes = tree["nodes"]
    for k in [k for k in nodes if k.startswith(PFX)]:
        del nodes[k]
    pub = {k: v for k, v in pub.items() if not k.startswith(PFX)}
    row_of = {r[1]: r for r in rows}
    towns, cities = Towns(5000), Towns(30000)

    places = []  # (props, geometry, details)
    redraw = []  # existing appellations drawn again: (props, geometry)
    old_count = {}

    for reg, R in spec["regions"].items():
        group = "g:IT/" + reg
        # the appellations of the region, by their atlas name (the search row name and the EU register name)
        ids = []

        def walk(k):
            for c in nodes[k][3]:
                if c.startswith("g:IT/" + reg + "/"):
                    walk(c)
                elif c.startswith("it-eupdo-"):
                    ids.append(c)
        walk(group)
        by_name = {}
        for k in ids:
            by_name[pub[k]["official_name"]] = k
            by_name[row_of[k][0]] = k
        apps = R["appellations"]
        missing = [a for a in apps if a not in by_name]
        assert not missing, f"{reg}: appellations not in the atlas: {missing}"
        nameof = {k: row_of[k][0] for k in ids}

        # 1. the appellation records
        for a, v in apps.items():
            k = by_name[a]
            d = pub[k]
            for f in ("vine_area_ha", "vine_area_src", "vine_area_note", "grape_share", "grape_share_note"):
                if v.get(f) is not None:
                    d[f] = v[f]
            if v.get("atlas_note") and not d.get("atlas_note"):
                d["atlas_note"] = v["atlas_note"]
            rules = []
            if v.get("doc_year"):
                rules.append(["DOC", str(v["doc_year"])])
            if v.get("docg_year"):
                rules.append(["DOCG", str(v["docg_year"])])
            rules += [list(x) for x in v.get("rules", [])]
            if rules:
                d["rules"] = rules
            if v.get("named_sites"):
                d["named_sites"] = v["named_sites"]
            if v.get("refs"):
                d["refs"] = v["refs"]
            if v.get("deep_level") in ("docg", "regional"):
                d["deep_open"] = True
            else:
                d.pop("deep_open", None)
            # a rank the EU inventory does not know yet (Terre Alfieri, DOCG since 2020)
            want = "docg" if v.get("rank") == "docg" else ""
            geom = None
            if v.get("communes"):  # communes corrected by the specification (Chianti Classico)
                d["communes"] = v["communes"]
                if v.get("partial_communes"):
                    d["partial_communes"] = v["partial_communes"]
                geom = com.union(v["communes"])
            if row_of[k][4] != want or geom is not None:
                if geom is None:
                    cs = d.get("communes") or []
                    if not cs or not all(com.key(c) for c in cs):
                        print(f"  {a}: rank {want or 'DOC'} kept off the map (communes not all matched)")
                        row_of[k][4] = want
                        continue
                    geom = com.union(cs)
                row_of[k][4] = want
                g = round_geom(geom.simplify(0.0004, preserve_topology=True), 5)
                c = centre(g)
                d["lat"], d["lon"] = round(c.y, 5), round(c.x, 5)
                d["outline_area_ha"] = ha_of(g)
                d["extent_km"] = extent_km(g)
                row_of[k][6] = bbox(g)
                redraw.append(({"id": k, "name": row_of[k][0], "country": "IT", "level": "appellation", "rank": want,
                                "parent": "", "src": "eupdo"}, g))

        # 2. the cru communes (Barolo, Barbaresco, Roero): one place per appellation and commune
        kids = {}  # appellation id -> [child ids]
        for cname, cv in R.get("communes", {}).items():
            for a in cv["of"]:
                k = by_name[a]
                pid = PFX + slug(a) + "-" + slug(cname)
                partial = a in cv.get("partial", [])
                g = round_geom(com.get(cname).simplify(0.0002, preserve_topology=True), 5)
                mga = cv.get("mga", {}).get(a, [])
                d = {"type": "Commune", "appellation_of": nameof[k], "communes": [com.name[com.key(cname)]],
                     "category": "Wine", "grapes": pub[k].get("grapes")}
                ha = (cv.get("vine_area_ha") or {}).get(a)
                if ha:
                    d["vine_area_ha"] = ha
                    d["vine_area_src"] = cv.get("vine_area_src", "")
                rules = [list(x) for x in (cv.get("rules") or {}).get(a, [])]
                if rules:
                    d["rules"] = rules
                if cv.get("atlas_note"):
                    d["atlas_note"] = cv["atlas_note"]
                if mga:
                    d["named_sites"] = {"kind": "MGA", "items": [[m, ""] for m in mga],
                                        "notes": (cv.get("mga_notes") or {}).get(a, [])}
                d["refs"] = cv.get("refs") or apps.get(a, {}).get("refs") or []
                d["outline_quality"] = "approx"
                d["outline"] = (PARTIAL_OUTLINE if partial else COMMUNE_OUTLINE).format(app=nameof[k])
                d["outline_area_ha"] = ha_of(g)
                d["outline_source"] = OUTLINE_SRC
                places.append(({"id": pid, "name": cv.get("display", com.name[com.key(cname)]), "country": "IT", "level": "subzone",
                                "rank": "", "parent": nameof[k], "src": SRC, "ol": "approx"}, g, d))
                kids.setdefault(k, []).append((pid, ha or 0))

        # 3. sub-zones: drawn on whole communes, or a marker on their village
        for sname, sv in R.get("subzones", {}).items():
            a = sv["of"]
            k = by_name[a]
            pid = PFX + slug(a) + "-" + slug(sv.get("display", sname))
            kind = sv["type"]
            d = {"type": {"Sottozona": "Sub-zone"}.get(kind, kind), "appellation_of": nameof[k], "category": "Wine", "grapes": pub[k].get("grapes")}
            if sv.get("communes"):
                d["communes"] = sv["communes"]
            for f in ("vine_area_ha", "vine_area_src", "vine_area_note", "grape_share", "grape_share_note", "atlas_note", "note"):
                if sv.get(f) is not None:
                    d[f] = sv[f]
            if sv.get("rules"):
                d["rules"] = [list(x) for x in sv["rules"]]
            if sv.get("named_sites"):
                d["named_sites"] = sv["named_sites"]
            d["refs"] = sv.get("refs") or apps.get(a, {}).get("refs") or []
            label = {"Sottozona": "sub-zone", "UGA": "UGA", "Pieve": "Pieve"}.get(kind, kind.lower())
            if sv.get("draw") == "communes":
                part = sv.get("partial_communes") or []
                g = round_geom(com.union(sv["communes"]).simplify(0.0004, preserve_topology=True), 5)
                d["outline_quality"] = "approx"
                d["outline"] = UNION_OUTLINE.format(kind=label, partial=(", " + str(len(part)) + " of them only in part" if part else ""))
                d["outline_area_ha"] = ha_of(g)
                d["outline_source"] = OUTLINE_SRC
                if part:
                    d["partial_communes"] = part
                ol = "approx"
            else:
                lat, lon = sv["lat"], sv["lon"]
                g = Point(round(lon, 5), round(lat, 5))
                d["outline_quality"] = "point"
                d["outline"] = POINT_OUTLINE.format(kind=label)
                if sv.get("loc_src"):
                    d["location_src"] = sv["loc_src"]
                if sv.get("village"):
                    d["village"] = sv["village"]
                ol = "point"
            places.append(({"id": pid, "name": sv.get("display", sname), "country": "IT", "level": "subzone", "rank": "",
                            "parent": nameof[k], "src": SRC, "ol": ol}, g, d))
            kids.setdefault(k, []).append((pid, sv.get("vine_area_ha") or 0))

        # 4. the tree: groups under the region, places under their appellation
        old_count[reg] = nodes[group][4]
        gids = []
        listed = set()
        for gr in R["groups"]:
            gid = group + "/" + slug(gr["name"])
            members = [by_name[a] for a in gr["members"]]
            listed |= set(members)
            # DOCG first, then by name
            members.sort(key=lambda m: (row_of[m][4] != "docg", norm(row_of[m][0])))
            bb = [row_of[m][6] for m in members]
            nodes[gid] = [gr["name"], "subregion", [min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb)],
                          members, 0]
            gids.append(gid)
        left = [k for k in ids if k not in listed]
        assert not left, f"{reg}: appellations in no group: {[row_of[k][0] for k in left]}"
        for k in [k for k in nodes if k.startswith(group + "/")]:
            if k not in gids:
                del nodes[k]
        nodes[group][3] = gids
        for k, ch in kids.items():
            ch.sort(key=lambda x: norm(row_of_new(places, x[0])))
            nodes[k] = [None, "place", None, [x[0] for x in ch], 0]

    # geometry facts, towns, wineries
    geoms = [g for _, g, _ in places]
    wins = wineries_in([g for g in geoms if g.geom_type != "Point"] or geoms)
    poly_idx = [i for i, g in enumerate(geoms) if g.geom_type != "Point"]
    wins = {poly_idx[j]: v for j, v in wins.items()} if wins else {}
    feats, details = [], {}
    for i, (p, g, d) in enumerate(places):
        c = centre(g)
        d["lat"], d["lon"] = round(c.y, 5), round(c.x, 5)
        if g.geom_type != "Point":
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
        details[p["id"]] = {k: v for k, v in d.items() if v is not None}
    for p, g in redraw:
        feats.append({"type": "Feature", "properties": p, "geometry": mapping(g)})

    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "it_deep.geojsonl"), "w", encoding="utf-8") as f:
        for ft in feats:
            f.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"  wrote {len(places)} new places and {len(redraw)} redrawn appellations -> build/it_deep.geojsonl")

    pub.update(details)
    with open(os.path.join(WEB, "details-it.json"), "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  details-it.json: {len(pub)} records")

    from build_index import ORDER
    for p, g, d in places:
        rows.append([p["name"], p["id"], "IT", p["level"], p["rank"], p["parent"], bbox(g.buffer(0.002) if g.geom_type == "Point" else g), ""])
    rows.sort(key=lambda r: (ORDER.get(r[3], 4), r[0]))
    with open(spath, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  search.json: {len(rows)} places")

    def total(k):
        n = nodes.get(k)
        if not n:
            return 0
        s = 0
        for c in n[3]:
            s += (total(c) if c.startswith("g:") else 1 + total(c))
        n[4] = s
        return s
    for reg in spec["regions"]:
        group = "g:IT/" + reg
        total(group)
        nodes["g:IT"][4] += nodes[group][4] - old_count[reg]
        print(f"  tree.json: {nodes[group][0]} {nodes[group][4]} places")
    json.dump(tree, open(tpath, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


def row_of_new(places, pid):
    for p, _, _ in places:
        if p["id"] == pid:
            return p["name"]
    return pid


if __name__ == "__main__":
    main()
