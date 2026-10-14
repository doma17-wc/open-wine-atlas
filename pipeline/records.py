"""Atlas records: the highest, steepest, largest, most northerly … places, worldwide and per country.

Reads the published web/data (search.json, details-*.json, after context.py and terrain_stats.py) and writes
web/data/records.json, which the Records tab of My atlas and the /records page show.

  {"cats": [{"key", "unit", "dir"}], "scopes": {"ALL": {cat: [[id, value], …]}, "FR": {…}, …}}

What counts:
  * regions are left out: records compare appellations, sub-zones and vineyards;
  * places drawn as a marker or from the administrative units that contain them (ol: point / approx), and the
    Swiss cantonal AOCs (a whole canton), are left out of the terrain, size and sea records, because their outline
    is not the wine area;
  * terrain records use the figures of terrain_stats.py, only for outlines drawn on the wine area itself (see drawn());
    slope only where the elevation cells are 35 m or finer;
  * the smallest places use measured areas only (area_ha), never the outline of whole communes.
"""
import glob
import json
import os
from collections import defaultdict

from common import ROOT

DATA = os.path.join(ROOT, "web", "data")
TOP_N = 10

CATS = [
    # key, unit, direction (-1 = highest value first), value function
    ("highest", "m", -1, lambda r, d: d.get("terrain", {}).get("e", [None, None])[1] if drawn(r, d) else None),
    ("lowest", "m", 1, lambda r, d: d.get("terrain", {}).get("e", [None, None])[1] if drawn(r, d) else None),
    ("steepest", "°", -1, lambda r, d: (d.get("terrain", {}).get("s") or [None])[0]
        if drawn(r, d) and d.get("terrain", {}).get("n", 0) >= 30 else None),
    ("largest", "ha", -1, lambda r, d: (d.get("area_ha") or d.get("outline_area_ha")) if real(r, d) else None),
    ("smallest", "ha", 1, lambda r, d: d.get("area_ha") if real(r, d) and (d.get("area_ha") or 0) > 0 else None),
    ("wineries", "", -1, lambda r, d: d.get("wineries_count")),
    ("inland", "km", -1, lambda r, d: d.get("sea_km") if real(r, d) and r[3] != "vineyard" else None),
    ("north", "°", -1, lambda r, d: d.get("lat") if r[3] != "vineyard" else None),
    ("south", "°", 1, lambda r, d: d.get("lat") if r[3] != "vineyard" else None),
]


def drawn(r, d):
    """The outline is the delimited wine area itself: French parcels (INAO), German Einzellagen and Großlagen,
    US AVA boundaries, the official Australian subregion layer. Outlines made of whole communes or districts
    (most of Europe, South America) take in mountains and plains with no vines, so their mean elevation and slope
    say little about the vineyards; they stay out of the terrain records."""
    return r[1].startswith(("fr-inao-", "de-rlp-", "us-ava-")) or bool(r[2] == "AU" and d.get("gi_url"))


def real(r, d):
    """The outline on the map is the wine area itself (or the communes the law names), not a stand-in."""
    if r[1].startswith("ch-canton-"):
        return False
    return d.get("outline_quality") not in ("approx", "point") and r[7] not in ("approx", "point")


def main():
    index = json.load(open(os.path.join(DATA, "search.json"), encoding="utf-8"))
    details = {}
    for f in glob.glob(os.path.join(DATA, "details-*.json")):
        details.update(json.load(open(f, encoding="utf-8")))
    vals = defaultdict(list)  # (scope, cat) -> [(value, id, name)]
    for r in index:
        if r[3] == "region":
            continue
        d = details.get(r[1])
        if not d:
            continue
        for key, _, _, fn in CATS:
            try:
                v = fn(r, d)
            except (TypeError, IndexError):
                v = None
            if v is None or v == "" or v == "na":
                continue
            v = float(v)
            vals[("ALL", key)].append((v, r[1], r[0]))
            vals[(r[2], key)].append((v, r[1], r[0]))
    scopes = defaultdict(dict)
    for (scope, key), rows in vals.items():
        direction = next(c[2] for c in CATS if c[0] == key)
        if len(rows) < 3:
            continue
        # one entry per name: Sonnenuhr is an Einzellage in five villages, show the best one only
        seen, top = set(), []
        for v, pid, name in sorted(rows, key=lambda x: (direction * x[0], x[2])):
            if name in seen:
                continue
            seen.add(name)
            top.append([pid, round(v, 2) if abs(v) < 100 else round(v)])
            if len(top) == TOP_N:
                break
        scopes[scope][key] = top
    out = {"cats": [{"key": k, "unit": u, "dir": dr} for k, u, dr, _ in CATS], "scopes": scopes}
    with open(os.path.join(DATA, "records.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("scopes:", len(scopes), "size:", os.path.getsize(os.path.join(DATA, "records.json")))


if __name__ == "__main__":
    main()
