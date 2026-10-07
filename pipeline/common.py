"""Shared helpers for the Open Wine Atlas data pipeline.

Every source is converted into the same open schema (see SCHEMA.md):

  Map feature properties (kept small, they go into vector tiles)
    id       stable id, "<country>-<source>-<source id>"
    name     official name
    country  ISO 3166-1 alpha-2
    level    region | appellation | subzone | vineyard | vineyard_area
    rank     grand_cru | premier_cru | docg | doca | pago | "" (optional)
    parent   name of the parent place ("" if none)
    src      source key from sources.json

  Place details (per country JSON, loaded when a place is opened)
    any extra attributes from the source: grapes, yields, communes, dates, links
"""
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
BUILD = os.path.join(ROOT, "build")
os.makedirs(BUILD, exist_ok=True)


def norm(s):
    """Lowercase ascii key for matching names across sources."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("’", "'")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def slug(s):
    return norm(s).replace(" ", "-")


def write_features(path, gdf, prop_cols):
    """Write a GeoDataFrame (EPSG:4326) as newline-delimited GeoJSON features."""
    from shapely.geometry import mapping
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for row in gdf.itertuples(index=False):
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            props = {c: getattr(row, c) for c in prop_cols}
            props = {k: ("" if v is None else v) for k, v in props.items()}
            f.write(json.dumps({"type": "Feature", "properties": props,
                                "geometry": mapping(geom)}, ensure_ascii=False,
                               separators=(",", ":")) + "\n")
            n += 1
    print(f"  wrote {n} features -> {os.path.relpath(path, ROOT)}")


def write_details(path, details):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  wrote {len(details)} detail records -> {os.path.relpath(path, ROOT)}")


def round_geom(geom, ndigits=6):
    """Round coordinates (6 decimals = ~0.1 m) to keep files compact."""
    from shapely import set_precision
    return set_precision(geom, 10 ** -ndigits)
