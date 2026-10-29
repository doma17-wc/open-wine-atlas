"""Bordeaux in depth: the classified estates as markers, and their lists on the appellation sheets.

Reads pipeline/lists/bordeaux_classified.json (editorial: the 1855 classification of the Médoc and of Sauternes and
Barsac, the Graves classification of 1959 and the Saint-Émilion classification of 2022, each estate with its rank,
appellation, commune and location) and writes:
  build/bordeaux_estates.geojsonl   one marker per estate (an estate in two classifications is one place)
  web/data/details-fr.json          the estates' facts; the appellations get their list of classified estates and
                                    the regional and sub-regional appellations stay open in the Deep Region
  web/data/search.json              search rows of the estates
  web/data/tree.json                estates under their appellation
Then: python pipeline/merge_overview.py build/bordeaux_estates.geojsonl --drop-src bxcc

Locations: the château's own coordinates on its Wikipedia article (French, else English) or its OpenStreetMap winery
point; the source of each is kept in the place details.
"""
import json
import os

from shapely.geometry import Point, mapping

from common import BUILD, ROOT, slug
from context import Towns, bearing, hav

WEB = os.path.join(ROOT, "web", "data")
LIST = os.path.join(ROOT, "pipeline", "lists", "bordeaux_classified.json")
SRC = "bxcc"
GROUP = "g:FR/bordeaux"
BX_REGIONAL = {"Bordeaux", "Bordeaux supérieur", "Crémant de Bordeaux"}
BX_SUBREG = {"Médoc", "Haut-Médoc", "Graves", "Graves supérieures", "Entre-deux-Mers", "Côtes de Bordeaux",
             "Côtes de Bordeaux-Saint-Macaire", "Premières Côtes de Bordeaux", "Blaye", "Côtes de Blaye"}
# rank -> short label for the map and the lists
SHORT = {
    "Premier Grand Cru Classé": "1855 · 1er", "Deuxième Cru": "1855 · 2e", "Troisième Cru": "1855 · 3e",
    "Quatrième Cru": "1855 · 4e", "Cinquième Cru": "1855 · 5e",
    "Premier Cru Supérieur": "1855 · 1er supérieur", "Premier Cru": "1855 · 1er", "Deuxième Cru (Sauternes)": "1855 · 2e",
    "Premier Grand Cru Classé A": "Saint-Émilion · 1er A", "Premier Grand Cru Classé (Saint-Émilion)": "Saint-Émilion · 1er",
    "Grand Cru Classé": "Saint-Émilion · GCC",
}


def main():
    spec = json.load(open(LIST, encoding="utf-8"))
    rows = json.load(open(os.path.join(WEB, "search.json"), encoding="utf-8"))
    tree = json.load(open(os.path.join(WEB, "tree.json"), encoding="utf-8"))
    nodes = tree["nodes"]
    pub = json.load(open(os.path.join(WEB, "details-fr.json"), encoding="utf-8"))
    towns = Towns(5000)

    # the appellations of Bordeaux by name
    bx_ids = set()
    def walk(k):
        for c in nodes.get(k, [None, None, None, []])[3]:
            if c.startswith("g:"):
                walk(c)
            elif not c.startswith("fr-bxcc-"):
                bx_ids.add(c)
    walk(GROUP)
    app = {r[0]: r[1] for r in rows if r[1] in bx_ids}

    estates = {}  # id -> record
    for ck, cl in spec["classifications"].items():
        for e in cl["estates"]:
            eid = "fr-bxcc-" + slug(e.get("key") or e["name"])
            rec = estates.setdefault(eid, {"name": e["name"], "classes": [], "appellation": e["appellation"], "commune": e["commune"],
                                           "loc": e.get("loc"), "web": e.get("web", ""), "aka": e.get("aka", "")})
            rec["classes"].append([cl["title"], e["rank"], cl.get("year_label") or cl.get("year"), e.get("short") or cl["short"].get(e["rank"], ""), ck])
            if e.get("loc") and not rec["loc"]:
                rec["loc"] = e["loc"]

    feats, details = [], {}
    by_app = {}
    for eid, e in estates.items():
        assert e["loc"], f"no location for {e['name']}"
        lat, lon, loc_src = e["loc"]
        a = e["appellation"]
        assert a in app, f"{e['name']}: appellation not in the map: {a}"
        first = e["classes"][0]
        top = any(c[4] in spec.get("open_ranks", {}) and c[1] in spec["open_ranks"][c[4]] for c in e["classes"])
        d = {"type": "Classified estate", "appellation_of": a, "communes": [e["commune"]],
             "classifications": [[c[0], c[1], c[2]] for c in e["classes"]],
             "class_short": first[3], "lat": round(lat, 5), "lon": round(lon, 5),
             "outline_quality": "point",
             "outline": "Location of the château. The vines of an estate are often spread over several plots around it.",
             "location_src": loc_src}
        if top:
            d["deep_open"] = True
        notes = [spec["classifications"][c[4]].get("estate_note") for c in e["classes"]]
        if any(notes):
            d["class_note"] = " ".join(n for n in notes if n)
        if e.get("aka"):
            d["aka"] = e["aka"]
        if e.get("web"):
            d["refs"] = [[e["name"], e["web"]]]
        t = towns.nearest(lat, lon)
        if t:
            d["near_town"] = [t["name"], round(hav(t["latitude"], t["longitude"], lat, lon), 1), bearing(t["latitude"], t["longitude"], lat, lon)]
        p = {"id": eid, "name": e["name"], "country": "FR", "level": "vineyard", "rank": "", "parent": a, "src": SRC, "ol": "point"}
        feats.append({"type": "Feature", "properties": p, "geometry": mapping(Point(round(lon, 5), round(lat, 5)))})
        details[eid] = d
        by_app.setdefault(a, []).append((eid, e["name"], first[3], [c[4] for c in e["classes"]], first[1]))

    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "bordeaux_estates.geojsonl"), "w", encoding="utf-8") as f:
        for ft in feats:
            f.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"  wrote {len(feats)} estates -> build/bordeaux_estates.geojsonl")

    # rank order inside an appellation: the order of the classification lists
    order = {}
    for ck, cl in spec["classifications"].items():
        for i, r in enumerate(cl["ranks"]):
            order[(ck, r)] = i

    pub = {k: v for k, v in pub.items() if not k.startswith("fr-bxcc-")}
    for name, aid in app.items():
        rec = pub.get(aid)
        if rec is None:
            continue
        for k in ("estates", "estates_note", "deep_open"):
            rec.pop(k, None)
        if name in BX_REGIONAL or name in BX_SUBREG:
            rec["deep_open"] = True
        es = by_app.get(name)
        if es:
            es.sort(key=lambda x: (min(order.get((ck, x[4]), 9) for ck in x[3]), slug(x[1])))
            rec["estates"] = [[eid, n, s] for eid, n, s, _, _ in es]
            if spec.get("app_notes", {}).get(name):
                rec["estates_note"] = spec["app_notes"][name]
    for k, v in spec.get("app_notes_only", {}).items():
        if k in app:
            pub[app[k]]["estates_note"] = v
    pub.update(details)
    with open(os.path.join(WEB, "details-fr.json"), "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  details-fr.json: {len(pub)} records")

    from build_index import ORDER
    rows = [r for r in rows if not str(r[1]).startswith("fr-bxcc-")]
    for ft in feats:
        p = ft["properties"]
        lon, lat = ft["geometry"]["coordinates"]
        d = details[p["id"]]
        rows.append([p["name"], p["id"], "FR", p["level"], p["rank"], p["parent"], [lon, lat, lon, lat], d.get("aka", "")])
    rows.sort(key=lambda r: (ORDER.get(r[3], 4), r[0]))
    with open(os.path.join(WEB, "search.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  search.json: {len(rows)} places")

    # tree: estates under their appellation, after any places already there
    for k, n in list(nodes.items()):
        if n[3] and any(c.startswith("fr-bxcc-") for c in n[3]):
            n[3] = [c for c in n[3] if not c.startswith("fr-bxcc-")]
            if not n[3] and n[0] is None and n[1] == "place":
                del nodes[k]
    for k in [k for k in nodes if k.startswith("fr-bxcc-")]:
        del nodes[k]
    for name, es in by_app.items():
        aid = app[name]
        if aid not in nodes:
            nodes[aid] = [None, "place", None, [], 0]
        nodes[aid][3] = nodes[aid][3] + [x[0] for x in es]

    def total(k):
        n = nodes.get(k)
        if not n:
            return 0
        s = 0
        for c in n[3]:
            s += (total(c) if c.startswith("g:") else 1 + total(c))
        n[4] = s
        return s
    old = nodes[GROUP][4]
    total(GROUP)
    nodes["g:FR"][4] += nodes[GROUP][4] - old
    json.dump(tree, open(os.path.join(WEB, "tree.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"  tree.json: Bordeaux {nodes[GROUP][4]} places")


if __name__ == "__main__":
    main()
