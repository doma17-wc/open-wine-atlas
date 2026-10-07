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
         "ch_appellations.geojsonl", "de_einzellagen.geojsonl", "de_grosslagen.geojsonl"]
ORDER = {"region": 0, "appellation": 1, "subzone": 2, "vineyard": 3}


def build_index():
    de = json.load(open(os.path.join(BUILD, "de_details.json"), encoding="utf-8"))
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
                index.append([p["name"], p["id"], p["country"], p["level"], p["rank"], p["parent"], b, alt])
    index.sort(key=lambda r: (ORDER.get(r[3], 4), r[0]))
    with open(os.path.join(WEB, "search.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  search.json: {len(index)} places")


if __name__ == "__main__":
    build_index()
