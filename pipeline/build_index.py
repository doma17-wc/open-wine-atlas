"""Search index: [name, id, country, level, rank, parent, bbox, alt].

`alt` holds extra search words, e.g. the commune of a German Einzellage, so that
"Wehlener Sonnenuhr" finds the Lage "Sonnenuhr" in Wehlen.
"""
import json
import os

from shapely.geometry import shape

from common import BUILD, ROOT

WEB = os.path.join(ROOT, "web", "data")
FILES = ["fr_appellations.geojsonl", "fr_denominations.geojsonl", "eu_appellations.geojsonl",
         "ch_appellations.geojsonl", "de_einzellagen.geojsonl", "de_grosslagen.geojsonl", "us_appellations.geojsonl",
         "world_appellations.geojsonl"]
ORDER = {"region": 0, "appellation": 1, "subzone": 2, "vineyard": 3}


def world_alt(p, d):
    """Extra search words for world.py places: Australian state, and the English country name."""
    words = [d.get("state", "")]
    return ", ".join(w for w in words if w)


def index_row(ft, alt=""):
    p = ft["properties"]
    b = [round(x, 4) for x in shape(ft["geometry"]).bounds]
    return [p["name"], p["id"], p["country"], p["level"], p["rank"], p["parent"], b, alt]


def build_index():
    de = json.load(open(os.path.join(BUILD, "de_details.json"), encoding="utf-8"))
    wpath = os.path.join(BUILD, "world_details.json")
    world = json.load(open(wpath, encoding="utf-8")) if os.path.exists(wpath) else {}
    index = []
    for name in FILES:
        path = os.path.join(BUILD, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                ft = json.loads(line)
                p = ft["properties"]
                b = [round(x, 4) for x in shape(ft["geometry"]).bounds]
                alt = ""
                if p["src"] == "rlp" and p["level"] == "vineyard":
                    d = de.get(p["id"], {})
                    alt = ", ".join(dict.fromkeys(d.get("gemarkungen", []) + d.get("communes", [])))
                elif p["id"] in world:
                    alt = world_alt(p, world[p["id"]])
                index.append([p["name"], p["id"], p["country"], p["level"], p["rank"], p["parent"], b, alt])
    index.sort(key=lambda r: (ORDER.get(r[3], 4), r[0]))
    with open(os.path.join(WEB, "search.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  search.json: {len(index)} places")


if __name__ == "__main__":
    build_index()
