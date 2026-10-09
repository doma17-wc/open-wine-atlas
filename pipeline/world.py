"""Wine places outside the EU and the US: Australia, New Zealand, South Africa, South America, Canada,
Mexico, the Caucasus, Eastern Europe, the Balkans outside the EU, the Middle East and Asia.

Two kinds of source:
  * world_specs.py: places defined through administrative units (geoBoundaries gbOpen, Runfola et al. 2020),
    or as a point at the namesake town when the place is far smaller than any unit.
  * Australia: GI outlines from adynak/WineRegions (CC0 as published there; the boundaries derive from
    Wine Australia's GI register, so Wine Australia is credited). Outlines cut at 5,000 vertices in that
    copy are shown as a point until the official Wine Australia layer (CC BY 4.0) replaces them.

Input : raw/geoboundaries/*.geojson, raw/geoboundaries/meta.csv, raw/au/*.geojson (pipeline/fetch_world.py)
Output: build/world_appellations.geojsonl, build/world_details.json
Every feature carries `ol`: legal (outline = the units the law names), approx (units approximate the
legal area), point (marker at the namesake town; no outline).
"""
import csv
import glob
import re
import json
import math
import os
import sys

import shapely
from pyproj import Geod
from shapely.geometry import Point, mapping, shape

from common import BUILD, RAW, norm, round_geom, slug, write_details
from world_specs import SPECS

GEOD = Geod(ellps="WGS84")
OUTLINE_TEXT = {
    "legal": "Built from the administrative units that the legal definition names.",
    "approx": "Built from the administrative units that contain the area. The legal boundary follows other lines (roads, rivers, farms or altitude), so the real area is smaller.",
    "point": "Shown as a point at the place it is named after. The registered area is much smaller than any administrative unit, and its boundary is not yet available as open data.",
    "au": "From the Wine Australia GI register, via the adynak/WineRegions copy.",
    "au_gap": "From the Wine Australia GI register, via the adynak/WineRegions copy. A short stretch of the boundary is missing in that copy and is closed with a straight line; the official Wine Australia outline will replace it.",
    "au_point": "Shown as a point: the copy of this boundary available to the atlas is incomplete. The official Wine Australia outline will replace it.",
}


def fix_text(s):
    """geoBoundaries NZL names are UTF-8 read as Latin-1; repair them, leave others alone."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def area_ha(g):
    try:
        return abs(GEOD.geometry_area_perimeter(g)[0]) / 10000
    except Exception:
        return None


def label_point(g):
    try:
        part = max(getattr(g, "geoms", [g]), key=lambda x: x.area)
        return shapely.polylabel(part, tolerance=0.001)
    except Exception:
        return g.representative_point()


class Admin:
    def __init__(self):
        self.layers = {}
        self.meta = {}
        with open(os.path.join(RAW, "geoboundaries", "meta.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.meta[(r.get("boundaryISO"), r.get("boundaryType"))] = r

    def layer(self, key):
        if key not in self.layers:
            data = json.load(open(os.path.join(RAW, "geoboundaries", key + ".geojson"), encoding="utf-8"))
            feats = []
            for ft in data["features"]:
                if not ft.get("geometry"):
                    continue
                p = ft["properties"]
                g = shapely.make_valid(shape(ft["geometry"]))
                feats.append((fix_text(p.get("shapeName") or ""), p.get("shapeID"), g))
            self.layers[key] = feats
        return self.layers[key]

    def licence(self, key):
        iso, adm = key.split("-")
        m = self.meta.get((iso, adm), {})
        return {"name": f"geoBoundaries {iso} {adm}" + (f" ({m.get('boundaryYearRepresented')})" if m.get("boundaryYearRepresented") else ""),
                "licence": m.get("boundaryLicense") or "see geoBoundaries metadata",
                "source": m.get("boundarySource") or ""}

    def find(self, key, unit):
        feats = self.layer(key)
        if isinstance(unit, (list, tuple)) and unit and unit[0] == "@id":
            hit = [f for f in feats if f[1] == unit[1]]
            return hit[0] if hit else None
        name, near = (unit[0], (unit[1], unit[2])) if isinstance(unit, (list, tuple)) else (unit, None)
        name = fix_text(name)
        hit = [f for f in feats if f[0] == name]
        if not hit:
            hit = [f for f in feats if norm(f[0]) == norm(name)]
        if not hit:
            return None
        if len(hit) > 1 and near:
            hit.sort(key=lambda f: f[2].centroid.distance(Point(*near)))
        return hit[0]


def build_specs(admin, out, details, problems):
    for spec in SPECS:
        cc = spec["cc"]
        seen = set()
        for p in spec["places"]:
            adm = p.get("adm") or spec["adm"]
            ol = p.get("outline") or spec["outline"]
            units, parts = [], []
            if p.get("point"):
                lat, lon = p["point"]
                g, ol = Point(lon, lat), "point"
            else:
                for u in p["units"]:
                    hit = admin.find(adm, u)
                    if hit is None:
                        problems.append(f"{cc} {p['name']}: unit not found in {adm}: {u!r}")
                        continue
                    units.append(hit[0].strip())
                    parts.append(hit[2])
                if not parts:
                    problems.append(f"{cc} {p['name']}: no geometry")
                    continue
                g = shapely.make_valid(shapely.union_all(parts))
                g = g.simplify(0.0005, preserve_topology=True)
                if g.geom_type == "GeometryCollection":
                    g = shapely.union_all([x for x in g.geoms if x.geom_type in ("Polygon", "MultiPolygon")])
            pid = f"{cc.lower()}-world-{slug(p['name'])}"
            if pid in seen:
                pid += "-" + p["level"]
            seen.add(pid)
            out.append({"type": "Feature", "geometry": mapping(round_geom(g, 5)),
                        "properties": {"id": pid, "name": p["name"], "country": cc, "level": p["level"], "rank": "",
                                       "parent": p.get("parent") or "", "src": "geob" if ol != "point" else "marker", "ol": ol}})
            lp = g if ol == "point" else label_point(g)
            d = {"type": p.get("type") or spec["type"], "basis": spec["basis"], "outline": OUTLINE_TEXT[ol],
                 "outline_quality": ol, "note": p.get("note"),
                 "registered": p.get("registered") if re.match(r"^\d{4}", str(p.get("registered") or "")) else None,
                 "register_ref": None if re.match(r"^\d{4}", str(p.get("registered") or "")) else p.get("registered"),
                 "admin_units": sorted(set(units)) if units else None,
                 "outline_source": admin.licence(adm) if ol != "point" else None,
                 "outline_area_ha": round(area_ha(g)) if ol != "point" else None,
                 "also_registered": p.get("also_registered"),
                 "lat": round(lp.y, 5), "lon": round(lp.x, 5)}
            details[pid] = {k: v for k, v in d.items() if v not in (None, "", [])}


# ---------------------------------------------------------------- Australia
AU_ZONES = {norm(x) for x in ["Big Rivers", "Central Ranges", "Hunter Valley", "Northern Rivers", "Northern Slopes", "South Coast",
                              "Western Plains", "Central Victoria", "Gippsland", "North East Victoria", "North West Victoria",
                              "Port Phillip", "Western Victoria", "Barossa", "Far North", "Fleurieu", "Limestone Coast", "Lower Murray",
                              "Mount Lofty Ranges", "The Peninsulas", "Greater Perth", "South West Australia",
                              "Central Western Australia", "Eastern Plains, Inland and North of Western Australia",
                              "West Australian South East Coastal"]}
AU_SUB = {norm(x) for x in ["Broke Fordwich", "Pokolbin", "Upper Hunter Valley", "High Eden", "Lenswood", "Piccadilly Valley",
                            "Nagambie Lakes", "Great Western", "Albany", "Denmark", "Frankland River", "Mount Barker", "Porongurup",
                            "Swan Valley"]}
AU_STATES = {norm(x) for x in ["New South Wales", "New Souuth Wales", "Victoria", "South Australia", "Western Australia", "Queensland",
                               "Australia", "South Eastern Australia", "South West Australiia"]}
AU_FIX = {norm("South West Australiia"): "South West Australia"}


def build_australia(out, details):
    feats = {}
    for path in sorted(glob.glob(os.path.join(RAW, "au", "*.geojson"))):
        data = json.load(open(path, encoding="utf-8"))
        ft = data["features"][0] if "features" in data else data
        p = ft["properties"]
        name = str(p.get("name") or "").strip()
        if not name or norm(name) in feats or norm(name) in AU_STATES:
            continue
        g = shape(ft["geometry"])
        # this copy stops every ring at 5,000 vertices and closes it with a straight line: measure that line
        gap = max((math.dist(pg.exterior.coords[-2], pg.exterior.coords[0]) for pg in getattr(g, "geoms", [g])
                   if len(pg.exterior.coords) >= 5000), default=0)
        cut = (gap > 0.2, gap > 0.02)
        within = [AU_FIX.get(norm(w), w.strip()) for w in str(p.get("within") or "").split("|") if w.strip()]
        feats[norm(name)] = (name, shapely.make_valid(g), cut, within, p, os.path.basename(path).split("__")[0].replace("_", " "))
    names = {k: v[0] for k, v in feats.items()}
    for k, (name, g, cut, within, p, state) in feats.items():
        level = "region" if k in AU_ZONES else "subzone" if k in AU_SUB else "appellation"
        kind = "GI zone" if level == "region" else "GI subregion" if level == "subzone" else "GI region"
        if k == norm("Gippsland"):
            kind = "GI zone and region"
        parent = next((names[norm(w)] for w in within if norm(w) in names and norm(w) != k and norm(w) not in AU_STATES), "")
        if level == "region":
            parent = ""
        lp = label_point(g)
        broken, gap = cut
        geom = lp if broken else g.simplify(0.0002, preserve_topology=True)
        pid = "au-world-" + slug(name)
        ol = "point" if broken else "legal"
        out.append({"type": "Feature", "geometry": mapping(round_geom(geom, 5)),
                    "properties": {"id": pid, "name": name, "country": "AU", "level": level, "rank": "", "parent": parent,
                                   "src": "marker" if broken else "wa", "ol": ol}})
        d = {"type": kind + " (Wine Australia)", "state": state,
             "basis": "Wine Australia Act 2013; Register of Protected GIs and Other Terms.",
             "outline": OUTLINE_TEXT["au_point" if broken else "au_gap" if gap else "au"], "outline_quality": ol,
             "registered": str(p.get("created"))[:10] if p.get("created") not in (None, "None", "") else None,
             "outline_area_ha": None if broken else round(area_ha(g)),
             "contains": [c.strip() for c in str(p.get("contains") or "").split("|") if c.strip() and c.strip() != "None"] or None,
             "lat": round(lp.y, 5), "lon": round(lp.x, 5)}
        details[pid] = {k2: v for k2, v in d.items() if v not in (None, "", [])}
    # regions whose parent zone is not in `within`: find it spatially
    zones = [(f["properties"]["name"], shape(f["geometry"])) for f in out
             if f["properties"]["country"] == "AU" and f["properties"]["level"] == "region" and f["geometry"]["type"] != "Point"]
    for f in out:
        q = f["properties"]
        if q["country"] == "AU" and q["level"] == "appellation" and not q["parent"]:
            c = Point(details[q["id"]]["lon"], details[q["id"]]["lat"])
            hit = [n for n, z in zones if z.contains(c)]
            if hit:
                q["parent"] = hit[0]


def main():
    admin = Admin()
    out, details, problems = [], {}, []
    build_specs(admin, out, details, problems)
    build_australia(out, details)
    with open(os.path.join(BUILD, "world_appellations.geojsonl"), "w", encoding="utf-8") as f:
        for ft in out:
            f.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")
    write_details(os.path.join(BUILD, "world_details.json"), details)
    by = {}
    for ft in out:
        q = ft["properties"]
        by.setdefault(q["country"], {}).setdefault(q["ol"], 0)
        by[q["country"]][q["ol"]] += 1
    print("places:", len(out), by)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
