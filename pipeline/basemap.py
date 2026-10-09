"""World base map: country outlines, lakes and rivers (Natural Earth via world-atlas and geo-maps, public domain).

Input : raw/basemap/world-atlas-2.0.2 (npm world-atlas), raw/basemap/geo-maps-earth-{lakes,rivers}-10m-0.6.0
Output: build/base/{countries,lakes,rivers}.geojson
Needs : mapshaper (npm i mapshaper)
"""
import json
import os
import subprocess

from common import BUILD, RAW, ROOT

OUT = os.path.join(BUILD, "base")
MAPSHAPER = os.path.join(ROOT, "node_modules", ".bin", "mapshaper")


def run(*args):
    subprocess.run([MAPSHAPER, *args], check=True)


def unwrap(ring):
    """Make a ring continuous across the date line: no step longer than 180 degrees of longitude."""
    out, shift = [list(ring[0])], 0.0
    for a, b in zip(ring, ring[1:]):
        d = b[0] - a[0]
        if d > 180:
            shift -= 360
        elif d < -180:
            shift += 360
        out.append([b[0] + shift, b[1]])
    return out


def split_dateline(geom):
    """world-atlas keeps Russia and Fiji whole across 180 degrees (it is drawn for spherical d3 maps). In plain
    longitude that adds an edge running round the whole earth, which shows as a stray line on the flat map and a
    band across the globe. Unwrap the rings and cut them at the date line."""
    from shapely.affinity import translate
    from shapely.geometry import Polygon, box, mapping, shape
    from shapely.ops import unary_union

    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    parts = []
    for rings in polys:
        shell = unwrap(rings[0])
        mid = sum(p[0] for p in shell) / len(shell)
        holes = []
        for h in rings[1:]:
            h = unwrap(h)
            hm = sum(p[0] for p in h) / len(h)
            k = round((mid - hm) / 360)
            holes.append([[x + 360 * k, y] for x, y in h])
        parts.append(Polygon(shell, holes).buffer(0))
    whole = unary_union(parts)
    out = [whole.intersection(box(-180, -90, 180, 90))]
    for k in (-1, 1):
        piece = whole.intersection(box(-180 + 360 * k, -90, 180 + 360 * k, 90))
        if not piece.is_empty:
            out.append(translate(piece, xoff=-360 * k))
    merged = unary_union([g for g in out if not g.is_empty])
    # cutting can leave slivers of line along the box edge: keep only the areas
    polys = [g for g in getattr(merged, "geoms", [merged]) if g.geom_type in ("Polygon", "MultiPolygon")]
    return mapping(unary_union(polys))


def crosses_dateline(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return any(abs(a[0] - b[0]) > 180 for rings in polys for r in rings for a, b in zip(r, r[1:]))


def fix_dateline(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    fixed = []
    for feat in d["features"]:
        g = feat.get("geometry")
        if g and g["type"] in ("Polygon", "MultiPolygon") and crosses_dateline(g):
            feat["geometry"] = json.loads(json.dumps(split_dateline(g)))
            fixed.append(feat["properties"].get("name"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, separators=(",", ":"))
    print("  cut at the date line:", ", ".join(fixed) or "none")


def main():
    os.makedirs(OUT, exist_ok=True)
    wa = os.path.join(RAW, "basemap", "world-atlas-2.0.2", "package", "countries-10m.json")
    run("-i", wa, "-target", "countries", "-filter", "this.properties.name !== 'Antarctica'",
        "-o", os.path.join(OUT, "countries.geojson"), "format=geojson", "precision=0.00001")
    fix_dateline(os.path.join(OUT, "countries.geojson"))
    for kind in ("lakes", "rivers"):
        src = os.path.join(RAW, "basemap", f"geo-maps-earth-{kind}-10m-0.6.0", "package", "map.geo.json")
        run("-i", src, "-simplify", "30%", "keep-shapes", "-o", os.path.join(OUT, f"{kind}.geojson"),
            "format=geojson", "precision=0.00001")


if __name__ == "__main__":
    main()
