"""Towns for the "Tasted at" field of a tasting note: web/data/cities.json.

GeoNames towns of 5,000 people or more (CC BY 4.0), through the geonamescache package, as
[name, country code, lat, lon] rows, the biggest first so the search can stop at the first matches.
Coordinates are rounded to 0.01 degree: a note is placed in its town, never at a precise spot.

    pip install geonamescache
    python3 pipeline/cities.py
"""
import json
import os

import geonamescache

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "web", "data", "cities.json")

rows = sorted(geonamescache.GeonamesCache().get_cities().values(), key=lambda c: -(c.get("population") or 0))
# one row per town and country: districts such as "Zürich (Kreis 3)" are left out
data, seen = [], set()
for c in rows:
    name = c.get("name") or ""
    if not name or "(" in name or (name, c["countrycode"]) in seen:
        continue
    seen.add((name, c["countrycode"]))
    data.append([name, c["countrycode"], round(c["latitude"], 2), round(c["longitude"], 2)])
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
print(len(data), "towns,", os.path.getsize(out), "bytes")
