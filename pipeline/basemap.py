"""World base map: country outlines, lakes and rivers (Natural Earth via world-atlas and geo-maps, public domain).

Input : raw/basemap/world-atlas-2.0.2 (npm world-atlas), raw/basemap/geo-maps-earth-{lakes,rivers}-10m-0.6.0
Output: build/base/{countries,lakes,rivers}.geojson
Needs : mapshaper (npm i mapshaper)
"""
import os
import subprocess

from common import BUILD, RAW, ROOT

OUT = os.path.join(BUILD, "base")
MAPSHAPER = os.path.join(ROOT, "node_modules", ".bin", "mapshaper")


def run(*args):
    subprocess.run([MAPSHAPER, *args], check=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    wa = os.path.join(RAW, "basemap", "world-atlas-2.0.2", "package", "countries-10m.json")
    run("-i", wa, "-target", "countries", "-filter", "this.properties.name !== 'Antarctica'",
        "-o", os.path.join(OUT, "countries.geojson"), "format=geojson", "precision=0.00001")
    for kind in ("lakes", "rivers"):
        src = os.path.join(RAW, "basemap", f"geo-maps-earth-{kind}-10m-0.6.0", "package", "map.geo.json")
        run("-i", src, "-simplify", "30%", "keep-shapes", "-o", os.path.join(OUT, f"{kind}.geojson"),
            "format=geojson", "precision=0.00001")


if __name__ == "__main__":
    main()
