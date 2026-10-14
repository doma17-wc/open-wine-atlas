"""Where each place is: towns, the sea, rivers, lakes and its latitude twins.

Runs on top of the published web/data (search.json and details-*.json), so it needs no other build step.
For every place with a centre it adds to its details record:

  near_town   [name, km, bearing]        nearest town of 5,000 people or more (GeoNames, CC BY 4.0)
  near_city   [name, km, bearing, pop]   nearest city of 30,000 people or more (GeoNames, CC BY 4.0)
  sea_km      distance from the centre to the nearest sea coast (Natural Earth, public domain)
  rivers      [[name, km], …]            named rivers near the place (Natural Earth, public domain)
  lakes       [[name, km], …]            named lakes within 30 km (Natural Earth, public domain)
  lat_twins   [id, …]                    wine regions and appellations on other continents at the same latitude

Bearings are the direction of the place as seen from the town (so "12 km SW of Beaune").
Distances are great-circle distances in km from the place centre; for rivers and lakes the nearest point
of the line or the shore.

Raw files (not committed, see sources.json):
  raw/geonames/cities5000.json   GeoNames cities5000, via the geonamescache package
  raw/ne/ne_10m_*.geojson        Natural Earth 1:10m vector (github.com/nvkelso/natural-earth-vector)

Run:  python pipeline/context.py      (then python web/build_web.py)
"""
import glob
import json
import math
import os
import re

import numpy as np
from shapely.geometry import Point, shape
from shapely.ops import nearest_points
from shapely.strtree import STRtree

from common import RAW, ROOT, norm

DATA = os.path.join(ROOT, "web", "data")
R = 6371.0088
SECT16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
CONTINENT = {
    "FR": "eu", "IT": "eu", "ES": "eu", "DE": "eu", "AT": "eu", "PT": "eu", "GR": "eu", "HU": "eu", "RO": "eu", "BG": "eu",
    "HR": "eu", "SI": "eu", "CZ": "eu", "SK": "eu", "BE": "eu", "CY": "eu", "NL": "eu", "GB": "eu", "MT": "eu", "DK": "eu",
    "LU": "eu", "CH": "eu", "RS": "eu", "MK": "eu", "ME": "eu", "BA": "eu", "MD": "eu", "UA": "eu",
    "GE": "as", "AM": "as", "TR": "as", "IL": "as", "LB": "as", "JP": "as", "CN": "as", "IN": "as",
    "US": "na", "CA": "na", "MX": "na",
    "CL": "sa", "AR": "sa", "BR": "sa", "UY": "sa",
    "AU": "oc", "NZ": "oc", "ZA": "af",
}

# Rivers and lakes keep their English Natural Earth name, like the rest of the interface. Natural Earth has local
# names for only part of its lines, so mixing them would give Hernád on one sheet and Danube on the next.
LOCAL = {}


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(min(1, math.sqrt(a)))


def bearing(lat1, lon1, lat2, lon2):
    """Compass bearing from point 1 to point 2, 16 sectors."""
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    deg = (math.degrees(math.atan2(y, x)) + 360) % 360
    return SECT16[int(round(deg / 22.5)) % 16]


def load_lines(*names, name_field="name"):
    geoms, labels = [], []
    for n in names:
        path = os.path.join(RAW, "ne", n + ".geojson")
        if not os.path.exists(path):
            continue
        for ft in json.load(open(path, encoding="utf-8"))["features"]:
            pr = ft["properties"]
            label = pr.get("name_en") or pr.get(name_field) or ""
            if label:
                label = {"": label, **{l: pr["name_" + l] for l in LOCAL.values() if pr.get("name_" + l)}}
            if name_field and not label:
                continue
            if not ft.get("geometry"):
                continue
            g = shape(ft["geometry"])
            if g.is_empty:
                continue
            geoms.append(g)
            labels.append(label)
    return geoms, labels


def near_lines(tree, geoms, labels, lat, lon, max_km, seen_key=lambda s: s, lang=""):
    """Named lines (or polygons) within max_km of the point, nearest first, one entry per name."""
    pt = Point(lon, lat)
    deg = max_km / 111.0 / max(0.2, math.cos(math.radians(lat)))
    best = {}
    for i in tree.query(pt.buffer(deg)):
        g = geoms[i]
        q = nearest_points(pt, g)[1] if not g.contains(pt) else pt
        km = hav(lat, lon, q.y, q.x)
        if km <= max_km:
            lab = labels[i].get(lang) or labels[i][""]
            k = seen_key(labels[i][""])
            if k not in best or km < best[k][1]:
                best[k] = [lab, km]
    return sorted(best.values(), key=lambda x: x[1])


class Towns:
    def __init__(self, min_pop):
        d = json.load(open(os.path.join(RAW, "geonames", "cities5000.json"), encoding="utf-8"))
        # leave out city districts that GeoNames lists as places of their own (Circoscrizione VIII, 3. Bezirk …)
        district = re.compile(r"\d|^(Circo|Municipio|Arrondissement|Stadtbezirk|Bezirk|Distrito|District|Quartiere|Ortsbezirk)|\s[IVXLC]+$", re.I)
        rows = [v for v in d.values() if (v.get("population") or 0) >= min_pop and not district.search(v["name"])]
        for v in rows:  # GeoNames gives a few bilingual Swiss towns their German name; use the local one
            v["name"] = {"Sitten": "Sion", "Siders": "Sierre", "Freiburg": "Fribourg" if v.get("countrycode") == "CH" else "Freiburg"}.get(v["name"], v["name"])
        self.rows = rows
        self.xyz = np.array([self._xyz(v["latitude"], v["longitude"]) for v in rows])

    @staticmethod
    def _xyz(lat, lon):
        p, l = math.radians(lat), math.radians(lon)
        return (math.cos(p) * math.cos(l), math.cos(p) * math.sin(l), math.sin(p))

    def nearest(self, lat, lon, skip=None):
        """The best-known place close to the point: among those within 1.3 times (or 3 km beyond) the
        distance of the nearest one, the most populous. So Blenheim beats its own suburb, Adelaide its hills."""
        v = np.array(self._xyz(lat, lon))
        dots = self.xyz @ v
        order = np.argsort(-dots)[:40]
        rows = [self.rows[k] for k in order if self.rows[k]["name"] != skip]
        if not rows:
            return None
        km = [hav(lat, lon, r["latitude"], r["longitude"]) for r in rows]
        reach = max(km[0] * 1.3, km[0] + 3)
        return max((r for r, d in zip(rows, km) if d <= reach), key=lambda r: r["population"])


def main():
    index = json.load(open(os.path.join(DATA, "search.json"), encoding="utf-8"))
    files = sorted(glob.glob(os.path.join(DATA, "details-*.json")))
    details = {f: json.load(open(f, encoding="utf-8")) for f in files}
    where = {pid: f for f, dd in details.items() for pid in dd}

    towns, cities, big = Towns(5000), Towns(30000), Towns(100000)
    coast_g, _ = load_lines("ne_10m_coastline", name_field=None)
    coast_tree = STRtree(coast_g)
    riv_g, riv_l = load_lines("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_europe", "ne_10m_rivers_north_america")
    riv_tree = STRtree(riv_g)
    lake_g, lake_l = load_lines("ne_10m_lakes", "ne_10m_lakes_europe", "ne_10m_lakes_north_america")
    lake_tree = STRtree(lake_g)
    print("towns", len(towns.rows), "cities", len(cities.rows), "coast", len(coast_g), "rivers", len(riv_g), "lakes", len(lake_g))

    # candidates for latitude twins: regions and appellations, preferring ones with an editorial note or a top rank
    twin_pool = []
    for r in index:
        name, pid, cc, level, rank = r[0], r[1], r[2], r[3], r[4]
        if cc not in CONTINENT or not (level in ("region", "appellation") or (level == "subzone" and cc not in ("FR", "DE"))):
            continue
        d = details.get(where.get(pid), {}).get(pid, {})
        lat = d.get("lat") or (r[6][1] + r[6][3]) / 2
        score = (2 if d.get("atlas_note") else 0) + (1 if rank in ("docg", "doca", "grand_cru", "pago") else 0) + (1 if level == "region" else 0)
        twin_pool.append((lat, score, pid, cc))

    n = 0
    for r in index:
        pid, cc, bbox = r[1], r[2], r[6]
        f = where.get(pid)
        if not f:
            continue
        d = details[f][pid]
        lat, lon = d.get("lat"), d.get("lon")
        if lat is None or lon is None:
            lat, lon = (bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2
        # size of the place: half the diagonal of its box, in km
        half = hav(bbox[1], bbox[0], bbox[3], bbox[2]) / 2
        out = {}

        t = towns.nearest(lat, lon)
        out["near_town"] = [t["name"], round(hav(t["latitude"], t["longitude"], lat, lon), 1), bearing(t["latitude"], t["longitude"], lat, lon)]
        c = cities.nearest(lat, lon, skip=t["name"])
        if c and hav(c["latitude"], c["longitude"], lat, lon) < 2:
            c = big.nearest(lat, lon, skip=t["name"])
        if c:
            out["near_city"] = [c["name"], round(hav(c["latitude"], c["longitude"], lat, lon)), bearing(c["latitude"], c["longitude"], lat, lon), c["population"]]

        pt = Point(lon, lat)
        best = None
        for rad in (0.5, 2, 6, 20, 60):
            cand = coast_tree.query(pt.buffer(rad))
            if len(cand):
                for i in cand:
                    q = nearest_points(pt, coast_g[i])[1]
                    km = hav(lat, lon, q.y, q.x)
                    best = km if best is None else min(best, km)
                if best is not None and best < rad * 111 * 0.6:
                    break
        if best is not None:
            out["sea_km"] = round(best) if best >= 10 else round(best, 1)

        lang = LOCAL.get(cc, "")
        rivers = near_lines(riv_tree, riv_g, riv_l, lat, lon, min(25, max(6, half)), seen_key=norm, lang=lang)
        if rivers:
            out["rivers"] = [[nm, round(km, 1)] for nm, km in rivers[:4]]
        lakes = near_lines(lake_tree, lake_g, lake_l, lat, lon, 30, seen_key=norm, lang=lang)
        if lakes:
            out["lakes"] = [[nm, round(km, 1)] for nm, km in lakes[:3]]

        if r[3] in ("region", "appellation") or (r[3] == "subzone" and cc not in ("FR", "DE")):
            cont = CONTINENT.get(cc)
            twins = sorted((x for x in twin_pool if abs(x[0] - lat) <= 0.35 and CONTINENT.get(x[3]) != cont),
                           key=lambda x: (-x[1], abs(x[0] - lat)))
            picked, used = [], set()
            for x in twins:
                if x[3] in used:
                    continue
                used.add(x[3])
                picked.append(x[2])
                if len(picked) == 5:
                    break
            if picked:
                out["lat_twins"] = picked

        for k in ("near_town", "near_city", "sea_km", "rivers", "lakes", "lat_twins"):
            d.pop(k, None)
        d.update(out)
        n += 1

    for f, dd in details.items():
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(dd, fh, ensure_ascii=False, separators=(",", ":"))
    print("places with context:", n)


if __name__ == "__main__":
    main()
