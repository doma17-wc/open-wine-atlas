"""Generalised French appellation outlines for small zoom levels (streamed, one appellation at a time).

Parcel mosaics read as noise at country scale: simplify, close gaps of ~300 m, smooth again.
Output: build/fr_overview.geojsonl
"""
import json
import os

from shapely.geometry import mapping, shape

from common import BUILD

n = 0
with open(os.path.join(BUILD, "fr_appellations.geojsonl"), encoding="utf-8") as src, \
     open(os.path.join(BUILD, "fr_overview.geojsonl"), "w", encoding="utf-8") as out:
    for line in src:
        ft = json.loads(line)
        g = shape(ft["geometry"]).simplify(0.0005, preserve_topology=True)
        g = g.buffer(0.003, 1).buffer(-0.003, 1).simplify(0.0008, preserve_topology=True)
        if g.is_empty:
            continue
        ft["geometry"] = mapping(g)
        out.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")
        n += 1
        if n % 25 == 0:
            print(n, flush=True)
print("fr_overview:", n)
