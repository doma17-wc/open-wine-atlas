"""OpenStreetMap extracts (ODbL, © OpenStreetMap contributors) via openhistorymap/openwinemap.

Used for: Swiss vineyard areas (no open AOC boundaries yet) and winery points in every country
that openwinemap covers (44, see fetch_world.py).

Input : raw/osm/<CC>.geojson
Output: build/osm_vineyards.geojsonl  (CH only, landuse=vineyard polygons)
        build/osm_wineries.geojsonl   (points: wineries, all countries)
"""
import json
import os

from common import BUILD, RAW
from fetch_world import OWM_COUNTRIES

COUNTRIES = [c for c in OWM_COUNTRIES if os.path.exists(os.path.join(RAW, "osm", f"{c}.geojson"))]


def main():
    nv = nw = 0
    with open(os.path.join(BUILD, "osm_vineyards.geojsonl"), "w", encoding="utf-8") as fv, \
         open(os.path.join(BUILD, "osm_wineries.geojsonl"), "w", encoding="utf-8") as fw:
        for c in COUNTRIES:
            data = json.load(open(os.path.join(RAW, "osm", f"{c}.geojson"), encoding="utf-8"))
            for f in data["features"]:
                p, g = f["properties"], f["geometry"]
                tags = p.get("tags") or {}
                oid = f"{c.lower()}-osm-{p.get('osm_type', 'x')[0]}{p.get('osm_id')}"
                if g["type"] in ("Polygon", "MultiPolygon") and c == "CH" and tags.get("landuse") == "vineyard":
                    props = {"id": oid, "name": p.get("name") or tags.get("name") or "", "country": c,
                             "level": "vineyard_area", "rank": "", "parent": "", "src": "osm"}
                    fv.write(json.dumps({"type": "Feature", "properties": props, "geometry": g},
                                        ensure_ascii=False, separators=(",", ":")) + "\n"); nv += 1
                elif g["type"] == "Point" and (p.get("category") == "winery" or tags.get("craft") == "winery"):
                    name = p.get("name") or tags.get("name")
                    if not name:
                        continue
                    props = {"id": oid, "name": name, "country": c, "kind": "winery",
                             "web": tags.get("website") or tags.get("contact:website") or "", "src": "osm"}
                    fw.write(json.dumps({"type": "Feature", "properties": props, "geometry": g},
                                        ensure_ascii=False, separators=(",", ":")) + "\n"); nw += 1
    print(f"  CH vineyard areas: {nv}; wineries: {nw}")


if __name__ == "__main__":
    main()
