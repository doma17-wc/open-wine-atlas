"""Switzerland below the cantonal AOC: wine areas, communal appellations and grands crus.

Reads pipeline/lists/ch_regions.json (editorial, every figure with its source) and draws each place as the union
of the communes it covers (BFS GEOSTAT / swisstopo generalised municipal boundaries, swiss-maps 4.7.0). A commune
is much larger than its vineyards, so these outlines are marked approximate (dashed) and the planted vines come
from the vineyard layer of the map. Places smaller than a commune (Dézaley, Calamin, Geneva premiers crus) are
markers.

Runs on top of the published web/data, like build_world_web.py:
  build/ch_regions.geojsonl        the new places
  web/data/details-ch.json         their facts (and the refreshed facts of the cantonal AOCs they sit in)
  web/data/search.json             their search rows
Then: python pipeline/merge_overview.py build/ch_regions.geojsonl --drop-src chreg && python pipeline/ch_tree.py

Raw: raw/basemap/swiss/package/<year>/municipalities.shp (npm pack swiss-maps@4.7.0),
     raw/geonames/cities5000.json (geonamescache), web/data/poi.pmtiles (wineries).
"""
import gzip
import json
import math
import os

import mapbox_vector_tile as mvt
import pyogrio
import shapely
from pmtiles.reader import MmapSource, Reader
from shapely.geometry import Point, mapping, shape
from shapely.ops import nearest_points, polylabel

from common import BUILD, RAW, ROOT, round_geom, write_features
from context import Towns, bearing, hav

WEB = os.path.join(ROOT, "web", "data")
LIST = os.path.join(ROOT, "pipeline", "lists", "ch_regions.json")
SWISS = os.path.join(RAW, "basemap", "swiss", "package")
SRC = "chreg"
# Swiss lake names (swiss-maps) -> the Natural Earth names the map can highlight
LAKE_NE = {"Lac Léman": "Geneva", "Lac de Neuchâtel": "Neuchâtel", "Murtensee/Lac de Morat": "Murten", "Bielersee / Lac de Bienne": "Biel",
           "Zürichsee": "Zurich", "Vierwaldstättersee": "Lucerne", "Walensee": "Walensee", "Bodensee": "Constance", "Lago di Lugano": "Lugano"}
DISPLAY = {"Roveredo (GR)": "Roveredo", "Villette (Lavaux)": "Villette", "Saint-Saphorin (Lavaux)": "Saint-Saphorin"}


def communes(year):
    df = pyogrio.read_dataframe(os.path.join(SWISS, str(year), "municipalities.shp"), encoding="utf-8")
    # the .prj says which Swiss grid: LV03 (EPSG:21781) up to the early 2010s, LV95 (EPSG:2056) since
    if df.crs is None:
        df = df.set_crs(2056)
    lakes = pyogrio.read_dataframe(os.path.join(SWISS, str(year), "lakes.shp"), encoding="utf-8")
    if lakes.crs is None:
        lakes = lakes.set_crs(df.crs)
    return df, lakes


def wineries_in(geoms):
    """OSM wineries (poi.pmtiles, zoom 10) inside each outline: {index: [[name, web], ...]}."""
    r = Reader(MmapSource(open(os.path.join(WEB, "poi.pmtiles"), "rb")))
    z = 10
    n = 2 ** z
    w, s, e, nn = shapely.union_all([g.envelope for g in geoms]).bounds
    x0, x1 = int((w + 180) / 360 * n), int((e + 180) / 360 * n)
    ty = lambda lat: int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    pts = {}
    for x in range(x0, x1 + 1):
        for y in range(ty(nn), ty(s) + 1):
            raw = r.get(z, x, y)
            if not raw:
                continue
            dec = mvt.decode(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw, default_options={"y_coord_down": True})
            lay = dec.get("wineries")
            if not lay:
                continue
            ext = lay["extent"]
            for ft in lay["features"]:
                if ft["geometry"]["type"] != "Point":
                    continue
                px, py = ft["geometry"]["coordinates"]
                lon = (x + px / ext) / n * 360 - 180
                lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + py / ext) / n))))
                p = ft["properties"]
                pts[p.get("id") or (p.get("name"), round(lon, 4), round(lat, 4))] = (p.get("name", ""), p.get("web", ""), Point(lon, lat))
    out = {}
    for i, g in enumerate(geoms):
        if g.geom_type == "Point":
            continue
        inside = sorted({(nm, web) for nm, web, pt in pts.values() if nm and g.contains(pt)})
        if inside:
            out[i] = [list(t) for t in inside]
    return out


def shares(d):
    """grape_ha [[grape, ha]] -> grape_share [[grape, % of the planted area]]; the hectares go into the note."""
    gh = d.pop("grape_ha", None)
    if not gh:
        return
    tot = d.get("area_ha") or d.get("vine_area_ha")
    d["grape_share"] = [[g, round(100 * ha / tot, 1)] for g, ha in gh]
    if not d.get("grape_share_note"):
        src = d.get("area_src") or d.get("vine_area_src") or ""
        d["grape_share_note"] = "Share of the " + f"{tot:,.1f}" + " ha planted" + (", " + src if src else "") + \
            ". " + ", ".join(f"{g} {ha:g} ha" for g, ha in gh) + "."


def extent_km(g):
    w, s, e, n = g.bounds
    mid = (s + n) / 2
    return [round(hav(s, (w + e) / 2, n, (w + e) / 2), 2), round(hav(mid, w, mid, e), 2)]


def main():
    spec = json.load(open(LIST, encoding="utf-8"))
    years = {}
    feats, details = [], {}
    towns, cities = Towns(5000), Towns(30000)
    lakes_ll = None

    geoms = []
    for pl in spec["places"]:
        if "geometry_file" in pl:  # an outline drawn elsewhere (OpenStreetMap), see contrib/ch
            fc = json.load(open(os.path.join(ROOT, pl["geometry_file"]), encoding="utf-8"))
            g = round_geom(shapely.union_all([shape(f["geometry"]) for f in fc["features"]]), 6)
        elif "point" in pl:
            lat, lon = pl["point"]
            g = Point(lon, lat)
            names = pl.get("communes", [])
        else:
            year = pl.get("year", 2024)
            if year not in years:
                years[year] = communes(year)
            df, lakes = years[year]
            if lakes_ll is None:
                lakes_ll = lakes.to_crs(4326)
            names = pl["communes"]
            sel = df[df["name"].isin(names)]
            missing = set(names) - set(sel["name"])
            assert not missing, f"{pl['id']}: communes not found in {year}: {missing}"
            g = shapely.make_valid(shapely.union_all(sel.geometry.simplify(20, preserve_topology=True).tolist()))
            g = sel.iloc[:1].set_geometry([g], crs=df.crs).to_crs(4326).geometry.iloc[0]
            g = round_geom(g, 5)
        geoms.append(g)

    wins = wineries_in(geoms)
    if lakes_ll is None:
        lakes_ll = communes(2024)[1].to_crs(4326)

    for i, (pl, g) in enumerate(zip(spec["places"], geoms)):
        point = g.geom_type == "Point"
        p = {"id": pl["id"], "name": pl["name"], "country": "CH", "level": pl["level"], "rank": pl.get("rank", ""),
             "parent": pl["parent"], "src": SRC, "ol": "point" if point else "approx"}
        feats.append({"type": "Feature", "properties": p, "geometry": mapping(g)})

        d = dict(pl.get("d", {}))
        shown = [DISPLAY.get(c, c) for c in pl.get("communes", [])]
        if shown:
            d["communes"] = shown
        # official planted area goes to vine_area_ha, the outline keeps its own size
        if "area_ha" in d:
            d["vine_area_ha"] = d.pop("area_ha")
            d["vine_area_src"] = d.pop("area_src", None) or (d["refs"][0][0] if d.get("refs") else "")
            if "area_note" in d:
                d["vine_area_note"] = d.pop("area_note")
        shares(d)
        if "pinot_ha" in d and d.get("vine_area_ha"):
            pct = round(100 * d["pinot_ha"] / d["vine_area_ha"], 1)
            d["grape_share"] = [["Pinot Noir (Blauburgunder)", pct]]
            d["grape_share_note"] = f"Pinot Noir: {d.pop('pinot_ha')} of {d['vine_area_ha']} ha, Plantahof Rebbaustatistik 2025"
        extra_outline = d.pop("outline_extra", "")
        if point:
            d["outline_quality"] = "point"
            d["outline"] = d.get("outline") or "Smaller than a commune: shown as a marker until the cantonal vineyard cadastre is mapped."
            c = g
        else:
            d["outline_quality"] = "approx"
            if not d.get("outline"):
                d["outline"] = ("Union of the communes " if len(shown) > 1 else "The commune of ") + ", ".join(shown) + \
                    ". The vines are only part of it: the vineyard layer of the map shows where they are."
            if pl.get("year") and pl["year"] < 2024 and not pl.get("geometry_file"):
                d["outline"] += f" Former communes, drawn with their boundaries of {pl['year']}."
            if extra_outline:
                d["outline"] += " " + extra_outline
            k = 111.32 * math.cos(math.radians(g.centroid.y)) * 110.57 * 100
            d["outline_area_ha"] = round(g.area * k)
            d["extent_km"] = extent_km(g)
            c = polylabel(max(getattr(g, "geoms", [g]), key=lambda q: q.area), tolerance=0.0005)
        d["lat"], d["lon"] = round(c.y, 5), round(c.x, 5)
        if pl.get("outline_src") == "osm":
            d["outline_source"] = {"name": "OpenStreetMap contributors", "licence": "ODbL 1.0", "source": pl["geometry_file"]}
        elif not point:
            d["outline_source"] = {"name": "BFS GEOSTAT / swisstopo municipal boundaries" + (" (" + str(pl["year"]) + ")" if pl.get("year") else " 2024"),
                                   "licence": "Open use, attribution", "source": "swiss-maps 4.7.0"}
        t = towns.nearest(d["lat"], d["lon"])
        if t:
            d["near_town"] = [t["name"], round(hav(t["latitude"], t["longitude"], d["lat"], d["lon"]), 1), bearing(t["latitude"], t["longitude"], d["lat"], d["lon"])]
        ct = cities.nearest(d["lat"], d["lon"], skip=t["name"] if t else None)
        if ct:
            d["near_city"] = [ct["name"], round(hav(ct["latitude"], ct["longitude"], d["lat"], d["lon"])), bearing(ct["latitude"], ct["longitude"], d["lat"], d["lon"]), ct["population"]]
        pt = Point(d["lon"], d["lat"])
        lk = []
        for nm, lg in zip(lakes_ll["name"], lakes_ll.geometry):
            q = pt if lg.contains(pt) else nearest_points(pt, lg)[1]
            km = hav(d["lat"], d["lon"], q.y, q.x)
            if km <= 25 and nm in LAKE_NE:
                lk.append([LAKE_NE[nm], round(km, 1)])
        if lk:
            d["lakes"] = sorted(lk, key=lambda x: x[1])[:3]
        if i in wins:
            d["wineries_count"] = len(wins[i])
            d["wineries"] = wins[i][:40]
        details[pl["id"]] = d

    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "ch_regions.geojsonl"), "w", encoding="utf-8") as f:
        for ft in feats:
            f.write(json.dumps(ft, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"  wrote {len(feats)} places -> build/ch_regions.geojsonl")

    # details-ch.json: replace the regional places, refresh the cantonal AOCs
    path = os.path.join(WEB, "details-ch.json")
    pub = json.load(open(path, encoding="utf-8"))
    pub = {k: v for k, v in pub.items() if not k.startswith("ch-reg-")}
    for cid, extra in spec.get("cantons", {}).items():
        rec = pub[cid]
        if rec.get("note", "").startswith("Outline follows the canton boundary"):
            rec["note"] = "Outline follows the canton boundary. The wine areas and communal appellations inside are drawn by commune."
        extra = dict(extra)
        shares(extra)
        if "area_ha" in extra:
            rec["vine_area_ha"] = extra.pop("area_ha")
            rec["vine_area_src"] = extra.pop("area_src", None) or (extra["refs"][0][0] if extra.get("refs") else "")
            if "area_note" in extra:
                rec["vine_area_note"] = extra.pop("area_note")
        rec.update(extra)
    pub.update(details)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  details-ch.json: {len(pub)} records")

    # search.json: one row per place, same order rule as build_index.py
    from build_index import ORDER
    spath = os.path.join(WEB, "search.json")
    rows = [r for r in json.load(open(spath, encoding="utf-8")) if not str(r[1]).startswith("ch-reg-")]
    for ft in feats:
        p = ft["properties"]
        b = [round(x, 4) for x in shape(ft["geometry"]).bounds]
        d = details[p["id"]]
        alt = ", ".join(x for x in [d.get("aka", "")] + [c for c in d.get("communes", []) if c != p["name"]] if x)
        rows.append([p["name"], p["id"], "CH", p["level"], p["rank"], p["parent"], b, alt])
    rows.sort(key=lambda r: (ORDER.get(r[3], 4), r[0]))
    with open(spath, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  search.json: {len(rows)} places")


if __name__ == "__main__":
    main()
