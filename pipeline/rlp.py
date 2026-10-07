"""Germany (Rheinland-Pfalz): official Weinlagen register (Weinbergsrolle), dl-de/by-2-0,
© Landwirtschaftskammer Rheinland-Pfalz. Covers Mosel, Rheinhessen, Pfalz, Nahe, Mittelrhein, Ahr.

Input : raw/rlp/vineyards.dml.sql  (PostGIS dump, EWKB hex in EPSG:25832)
Output: build/de_einzellagen.geojsonl, build/de_grosslagen.geojsonl, build/de_details.json
"""
import os

import geopandas as gpd
import shapely

from common import BUILD, RAW, round_geom, write_details, write_features

SRC = "rlp"
COLS = ["ogc_fid", "wlg_nr", "datum", "suchfeld", "suchfeld_1", "anbaugebie", "bereich", "grosslage",
        "wlg_name", "gemeinde", "gemarkunge", "rebflache_", "gem_info", "gid", "wkb_geometry"]


def read_copy(path):
    rows, inside = [], False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("COPY public.vineyards"):
                inside = True
                continue
            if inside:
                if line.startswith("\\."):
                    break
                vals = [None if v == "\\N" else v for v in line.rstrip("\n").split("\t")]
                rows.append(dict(zip(COLS, vals)))
    return rows


def main():
    rows = read_copy(os.path.join(RAW, "rlp", "vineyards.dml.sql"))
    geoms = shapely.from_wkb([r.pop("wkb_geometry") for r in rows])
    gdf = gpd.GeoDataFrame(rows, geometry=shapely.make_valid(geoms), crs=25832)
    print("Einzellagen records:", len(gdf), gdf["anbaugebie"].value_counts().to_dict())

    # one feature per registered site number (a Lage can span several Gemarkungen)
    lagen = gdf.dissolve(by="wlg_nr", aggfunc={"wlg_name": "first", "anbaugebie": "first", "bereich": "first",
                                               "grosslage": "first", "gemeinde": lambda s: sorted(set(s.dropna())),
                                               "gemarkunge": lambda s: sorted(set(s.dropna())),
                                               "datum": "first"}).reset_index()
    lagen["geometry"] = lagen.geometry.simplify(1.0, preserve_topology=True)
    lagen["area_ha"] = (lagen.geometry.area / 10000).round(1)

    gross = gdf.dissolve(by=["anbaugebie", "grosslage"]).reset_index()[["anbaugebie", "grosslage", "bereich", "geometry"]]
    gross["geometry"] = gross.geometry.simplify(2.0, preserve_topology=True)

    details = {}
    lagen = lagen.to_crs(4326)
    lagen["geometry"] = [round_geom(g) for g in lagen.geometry]
    lagen["id"] = "de-rlp-" + lagen["wlg_nr"].astype(str)
    lagen["name"] = lagen["wlg_name"]
    lagen["country"] = "DE"
    lagen["level"] = "vineyard"
    lagen["rank"] = ""
    lagen["parent"] = lagen["anbaugebie"]
    lagen["src"] = SRC
    for r in lagen.itertuples():
        details[r.id] = {"type": "Einzellage", "region": r.anbaugebie, "bereich": r.bereich,
                         "grosslage": r.grosslage, "communes": r.gemeinde, "gemarkungen": r.gemarkunge, "area_ha": r.area_ha,
                         "register_no": r.wlg_nr, "source_date": r.datum}

    gross = gross[gross["grosslage"].notna() & (gross["grosslage"] != "")].to_crs(4326)
    gross["geometry"] = [round_geom(g) for g in gross.geometry]
    gross["id"] = ["de-rlp-gl-" + f"{a}-{g}".lower().replace(" ", "-") for a, g in zip(gross["anbaugebie"], gross["grosslage"])]
    gross["name"] = gross["grosslage"]
    gross["country"] = "DE"
    gross["level"] = "subzone"
    gross["rank"] = ""
    gross["parent"] = gross["anbaugebie"]
    gross["src"] = SRC
    for r in gross.itertuples():
        details[r.id] = {"type": "Großlage", "region": r.anbaugebie, "bereich": r.bereich}

    cols = ["id", "name", "country", "level", "rank", "parent", "src"]
    write_features(os.path.join(BUILD, "de_einzellagen.geojsonl"), lagen, cols)
    write_features(os.path.join(BUILD, "de_grosslagen.geojsonl"), gross, cols)
    write_details(os.path.join(BUILD, "de_details.json"), details)


if __name__ == "__main__":
    main()
