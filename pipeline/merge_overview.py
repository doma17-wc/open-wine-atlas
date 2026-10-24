"""Add places to the published overview.pmtiles without tippecanoe and without the other sources.

Used when one country gets new places (for example the Swiss sub-appellations from ch_regions.py) and the raw
data of the other countries is not at hand. Only the tiles that touch the new places are decoded, changed and
encoded again; every other tile is copied byte for byte.

  python pipeline/merge_overview.py build/ch_regions.geojsonl --drop-src chreg

  --drop-src   features of these source keys are removed first (so the script can run again)
  --bbox       area to touch, default: the bounds of the new features plus a margin

Outlines go to the "appellations" layer, one label point per place to "labels", with the same properties and
label zooms as build_tiles.py. Needs: pip install pmtiles mapbox-vector-tile shapely
"""
import argparse
import gzip
import json
import math
import os
import shutil
import sys

import mapbox_vector_tile as mvt
import shapely
from pmtiles.reader import MmapSource, Reader, all_tiles
from pmtiles.tile import Compression, TileType, zxy_to_tileid
from pmtiles.writer import Writer
from shapely.geometry import box, mapping, shape
from shapely.ops import polylabel, transform

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_tiles import POINT_MINZOOM, area_ha, label_minzoom, short_name  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OV = os.environ.get("OVERVIEW", os.path.join(ROOT, "web", "data", "overview.pmtiles"))
EXTENT = 4096
BUFFER = 64  # px of the tile extent, like tippecanoe's default buffer of 5/256
OUTLINE_MINZOOM = {"region": 2, "appellation": 5, "subzone": 7, "vineyard": 8}


def lonlat_to_px(z, x, y):
    n = 2 ** z

    def f(lon, lat, *_):
        import numpy as np
        lon, lat = np.asarray(lon), np.asarray(lat)
        px = ((lon + 180) / 360 * n - x) * EXTENT
        lat_r = np.radians(np.clip(lat, -85.0511, 85.0511))
        py = ((1 - np.arcsinh(np.tan(lat_r)) / math.pi) / 2 * n - y) * EXTENT
        return px, py
    return f


def tile_range(bounds, z):
    w, s, e, n = bounds
    k = 2 ** z
    x0 = int((w + 180) / 360 * k)
    x1 = int((e + 180) / 360 * k)
    y0 = int((1 - math.asinh(math.tan(math.radians(n))) / math.pi) / 2 * k)
    y1 = int((1 - math.asinh(math.tan(math.radians(s))) / math.pi) / 2 * k)
    for x in range(max(0, x0), min(k - 1, x1) + 1):
        for y in range(max(0, y0), min(k - 1, y1) + 1):
            yield x, y


def label_point(g):
    try:
        return polylabel(max(getattr(g, "geoms", [g]), key=lambda p: p.area), tolerance=0.0005)
    except Exception:
        return g.representative_point()


def prepare(path):
    """New features as (layer, minzoom, properties, lon/lat geometry)."""
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            ft = json.loads(line)
            p = ft["properties"]
            g = shape(ft["geometry"])
            if g.is_empty:
                continue
            if g.geom_type == "Point":
                out.append(("appellations", OUTLINE_MINZOOM.get(p["level"], 6), p, g))
                q = dict(p, ha=0, short=p["name"])
                out.append(("labels", POINT_MINZOOM.get(p["level"], 9), q, g))
                continue
            ha = area_ha(g)
            out.append(("appellations", OUTLINE_MINZOOM.get(p["level"], 6), p, g.simplify(0.0008, preserve_topology=True)))
            q = dict(p, ha=round(ha), short=short_name(p))
            out.append(("labels", label_minzoom(p["level"], ha, p["country"]), q, label_point(g)))
    return out


def encode_feature(layer_feats, layer, props, geom):
    if geom.is_empty:
        return
    layer_feats.setdefault(layer, []).append({"geometry": geom, "properties": props})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("features", nargs="+")
    ap.add_argument("--drop-src", default="")
    ap.add_argument("--ids-from", default="", help="also drop features whose id is in these geojsonl files")
    args = ap.parse_args()
    drop_src = set(filter(None, args.drop_src.split(",")))

    new = []
    for p in args.features:
        new += prepare(p)
    bounds = shapely.union_all([g.envelope for _, _, _, g in new]).bounds
    bounds = (bounds[0] - 0.2, bounds[1] - 0.2, bounds[2] + 0.2, bounds[3] + 0.2)
    new_ids = {p["id"] for _, _, p, _ in new}

    src_f = open(OV, "rb")
    reader = Reader(MmapSource(src_f))
    header, meta = reader.header(), reader.metadata()
    minz, maxz = header["min_zoom"], header["max_zoom"]

    touched = {}
    for z in range(minz, maxz + 1):
        for x, y in tile_range(bounds, z):
            touched[(z, x, y)] = None

    tiles = {}
    for (z, x, y), data in all_tiles(reader.get_bytes):
        tiles[(z, x, y)] = data

    changed = 0
    for (z, x, y) in touched:
        raw = tiles.get((z, x, y))
        layers, dropped = {}, 0
        if raw:
            dec = mvt.decode(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw,
                             default_options={"y_coord_down": True})
            for name, lay in dec.items():
                for ft in lay["features"]:
                    p = ft["properties"]
                    if p.get("src") in drop_src or p.get("id") in new_ids:
                        dropped += 1
                        continue
                    layers.setdefault(name, []).append({"geometry": shape(ft["geometry"]), "properties": p})
        to_px = lonlat_to_px(z, x, y)
        clip = box(-BUFFER, -BUFFER, EXTENT + BUFFER, EXTENT + BUFFER)
        added = 0
        for layer, mz, props, g in new:
            if z < mz:
                continue
            pg = transform(to_px, g)
            if pg.geom_type == "Point":
                if not clip.contains(pg):
                    continue
                encode_feature(layers, layer, props, pg)
                added += 1
                continue
            if not pg.intersects(clip):
                continue
            pg = shapely.make_valid(pg.intersection(clip).simplify(1.0, preserve_topology=True))
            pg = shapely.set_precision(pg, 1.0)
            polys = [q for q in getattr(pg, "geoms", [pg]) if q.geom_type in ("Polygon", "MultiPolygon") and not q.is_empty]
            if not polys:
                continue
            pg = shapely.union_all(polys)
            if pg.area < 2:
                continue
            encode_feature(layers, layer, props, pg)
            added += 1
        if not added and not dropped:
            continue  # nothing changes here: keep the tile byte for byte
        order = ["appellations", "labels"] + [k for k in layers if k not in ("appellations", "labels")]
        payload = [{"name": k, "features": layers[k]} for k in order if layers.get(k)]
        if not payload:
            tiles.pop((z, x, y), None)
            continue
        enc = mvt.encode(payload, default_options={"y_coord_down": True, "extents": EXTENT})
        tiles[(z, x, y)] = gzip.compress(enc, compresslevel=9)
        changed += 1

    tmp = OV + ".new"
    with open(tmp, "wb") as out:
        w = Writer(out)
        for key in sorted(tiles, key=lambda k: zxy_to_tileid(*k)):
            w.write_tile(zxy_to_tileid(*key), tiles[key])
        hdr = {k: header[k] for k in header if k not in ("root_offset", "root_length", "metadata_offset", "metadata_length",
                                                       "leaf_directory_offset", "leaf_directory_length", "tile_data_offset",
                                                       "tile_data_length", "addressed_tiles_count", "tile_entries_count",
                                                       "tile_contents_count", "clustered")}
        w.finalize(hdr, meta)
    src_f.close()
    shutil.move(tmp, OV)
    print(f"  overview.pmtiles: {changed} tiles rewritten, {len(new_ids)} places, {os.path.getsize(OV) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
