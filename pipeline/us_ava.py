"""United States: American Viticultural Areas (AVAs).

Source: UC Davis Library, AVA Digitizing Project (https://github.com/UCDavisLibrary/ava), CC0 1.0.
Boundaries are digitised from the legal descriptions in 27 CFR part 9.

Input : raw/ava/avas.geojson
Output: build/us_appellations.geojsonl, build/us_details.json
"""
import json
import os

import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

from common import BUILD, RAW, round_geom, write_details

SRC = "ava"
TO_M = Transformer.from_crs(4326, 5070, always_xy=True).transform  # NAD83 / Conus Albers, equal area


def split(v):
    return [x.strip() for x in str(v or "").split("|") if x.strip() and x.strip() != "None"]


def main():
    raw = json.load(open(os.path.join(RAW, "ava", "avas.geojson"), encoding="utf-8"))
    feats = []
    for ft in raw["features"]:
        p = ft["properties"]
        if p.get("removed") not in (None, "None", "") or p.get("valid_end") not in (None, "None", ""):
            continue  # an AVA that was revoked or superseded
        if not ft.get("geometry"):
            continue
        g = shapely.make_valid(shape(ft["geometry"]))
        if g.is_empty:
            continue
        feats.append((p, g))
    area = {p["name"]: transform(TO_M, g).area / 10000 for p, g in feats}

    out, details = [], {}
    for p, g in feats:
        within = [w for w in split(p.get("within")) if w in area]
        parent = min(within, key=lambda w: area[w]) if within else ""
        pid = "us-ava-" + p["ava_id"]
        out.append({"type": "Feature", "geometry": shapely.geometry.mapping(round_geom(g, 5)),
                    "properties": {"id": pid, "name": p["name"], "country": "US",
                                   "level": "subzone" if parent else "appellation", "rank": "",
                                   "parent": parent, "src": SRC}})
        cfr = str(p.get("cfr_index") or "")
        d = {
            "type": "AVA (American Viticultural Area)",
            "official_name": p["name"] + " viticultural area",
            "registered": p.get("created") if p.get("created") not in (None, "None") else None,
            "states": split(p.get("state")),
            "counties": sorted(set(split(p.get("county")))),
            "within": within,
            "contains": split(p.get("contains")),
            "aka": p.get("aka") if p.get("aka") not in (None, "None") else None,
            "petitioner": p.get("petitioner") if p.get("petitioner") not in (None, "None") else None,
            "cfr": ("27 CFR " + cfr) if cfr and cfr != "None" else None,
            "cfr_url": ("https://www.ecfr.gov/current/title-27/chapter-I/subchapter-A/part-9/subpart-C/section-" + cfr)
                       if cfr and cfr != "None" else None,
            "boundary_text": (str(p.get("boundary_description"))[:1400] + ("…" if len(str(p.get("boundary_description"))) > 1400 else ""))
                             if p.get("boundary_description") not in (None, "None") else None,
            "area_ha": round(area[p["name"]]),
        }
        details[pid] = {k: v for k, v in d.items() if v not in (None, "", [])}

    with open(os.path.join(BUILD, "us_appellations.geojsonl"), "w", encoding="utf-8") as f:
        for ft in out:
            f.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")
    write_details(os.path.join(BUILD, "us_details.json"), details)
    print("AVAs:", len(out), "of which nested:", sum(1 for f in out if f["properties"]["parent"]))


if __name__ == "__main__":
    main()
