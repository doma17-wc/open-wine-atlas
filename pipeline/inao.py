"""France: INAO 'Délimitation parcellaire des AOC viticoles' (Licence Ouverte 2.0).

Input : raw/inao/*delim-parcellaire-aoc-shp.shp  (one record per appellation x denomination x commune)
Output: build/fr_appellations.geojsonl   one feature per AOC (dissolved over communes)
        build/fr_denominations.geojsonl  one feature per 'dénomination géographique complémentaire'
                                         (premiers crus, climats, grand cru lieux-dits, sub-zones)
        build/fr_details.json
"""
import glob
import os

import geopandas as gpd
import pyogrio
import shapely

from common import BUILD, RAW, norm, round_geom, write_details, write_features

SRC = "inao"

# The 33 Burgundy grand cru appellations (incl. Chablis grand cru). Matched on normalised names.
BURGUNDY_GRAND_CRUS = [
    "Chambertin", "Chambertin-Clos de Bèze", "Chapelle-Chambertin", "Charmes-Chambertin",
    "Griotte-Chambertin", "Latricières-Chambertin", "Mazis-Chambertin", "Mazoyères-Chambertin",
    "Ruchottes-Chambertin", "Bonnes-Mares", "Clos de la Roche", "Clos Saint-Denis", "Clos de Tart",
    "Clos des Lambrays", "Musigny", "Clos de Vougeot", "Échezeaux", "Grands-Échezeaux",
    "La Grande Rue", "La Romanée", "La Tâche", "Richebourg", "Romanée-Conti", "Romanée-Saint-Vivant",
    "Corton", "Corton-Charlemagne", "Charlemagne", "Montrachet", "Bâtard-Montrachet",
    "Bienvenues-Bâtard-Montrachet", "Chevalier-Montrachet", "Criots-Bâtard-Montrachet",
    "Chablis grand cru",
]
GC_KEYS = {norm(n) for n in BURGUNDY_GRAND_CRUS}


def display_name(official):
    """INAO lists alternatives as 'A ou B'; the map shows the first form, details keep the full name."""
    return official.split(" ou ")[0].strip()


def denom_level(denom, app):
    """A named climat / lieu-dit is a vineyard; a broad complementary name is a sub-zone."""
    n = norm(denom)
    for key in (" premier cru ", " grand cru "):
        if key in f" {n} " and not n.endswith(key.strip()):
            return "vineyard"
    # climats inside a grand cru appellation, e.g. "Corton Les Bressandes"
    if rank_for(app) == "grand_cru" and norm(denom) != norm(app):
        return "vineyard"
    return "subzone"


def rank_for(app, denom=""):
    a, d = norm(app), norm(denom)
    if a in GC_KEYS or a.startswith("clos de vougeot") or " grand cru" in f" {a} " or " grand cru" in f" {d} ":
        return "grand_cru"
    if " premier cru" in f" {d} ":
        return "premier_cru"
    return ""


def _union(geoms):
    return shapely.union_all(shapely.make_valid(geoms), grid_size=0.1)


def dissolve(df, keys, agg):
    """Group rows, union geometries in parallel, keep first attributes and the commune list."""
    from multiprocessing import Pool
    groups = list(df.groupby(keys, sort=False))
    with Pool(os.cpu_count()) as pool:
        geoms = pool.map(_union, [g.geometry.values for _, g in groups], chunksize=1)
    rows = []
    for (key, g), geom in zip(groups, geoms):
        row = dict(zip(keys, key))
        for c, how in agg.items():
            row[c] = g[c].iloc[0]
        row["nomcom"] = sorted(set(g["nomcom"].dropna()))
        rows.append(row)
    return gpd.GeoDataFrame(rows, geometry=geoms, crs=df.crs)


def main():
    shp = glob.glob(os.path.join(RAW, "inao", "*delim-parcellaire-aoc-shp.shp"))[0]
    print("reading", os.path.basename(shp))
    gdf = pyogrio.read_dataframe(shp)
    # simplify each commune record first (1 m, Lambert-93): removes cadastral noise and makes
    # the dissolve below fast
    gdf["geometry"] = shapely.make_valid(shapely.simplify(gdf.geometry.values, 1.0, preserve_topology=True))
    dt = os.path.basename(shp)[:10]

    # ---- appellations: dissolve every record of an AOC (its base denomination rows)
    base = gdf[gdf["type_denom"] == "appellation"]
    apps = dissolve(base, ["id_app", "app"], {"categorie": "first", "signe": "first", "dt": "first"})
    print("appellations:", len(apps))

    # ---- complementary denominations (premier cru, climats, sub-zones)
    dgc = gdf[gdf["type_denom"] != "appellation"]
    dens = dissolve(dgc, ["id_denom", "denom", "id_app", "app"], {"categorie": "first"})
    print("denominations:", len(dens))

    details = {}

    def finish(df, kind):
        df = df.copy()
        # 1 m simplification in Lambert-93 removes cadastral noise but keeps parcel edges
        df["area_ha"] = (df.geometry.area / 10000).round(1)
        df = df.to_crs(4326)
        df["geometry"] = [round_geom(g) for g in df.geometry]
        df["country"] = "FR"
        df["src"] = SRC
        return df

    apps = finish(apps, "app")
    apps["id"] = "fr-inao-a" + apps["id_app"].astype(str)
    apps["name"] = [display_name(a) for a in apps["app"]]
    apps["level"] = "appellation"
    apps["rank"] = [rank_for(a) for a in apps["app"]]
    apps["parent"] = ""
    for r in apps.itertuples():
        details[r.id] = {"type": r.signe or "AOC", "official_name": r.app, "category": r.categorie, "area_ha": r.area_ha,
                         "communes": [c.title() for c in r.nomcom], "inao_office": r.dt,
                         "source_date": dt}

    dens = finish(dens, "denom")
    dens["id"] = "fr-inao-d" + dens["id_denom"].astype(str)
    dens["name"] = dens["denom"]
    dens["level"] = [denom_level(d, a) for d, a in zip(dens["denom"], dens["app"])]
    dens["rank"] = [rank_for(a, d) for a, d in zip(dens["app"], dens["denom"])]
    dens["parent"] = [display_name(a) for a in dens["app"]]
    for r in dens.itertuples():
        details[r.id] = {"type": "Dénomination géographique complémentaire", "category": r.categorie,
                         "area_ha": r.area_ha, "communes": [c.title() for c in r.nomcom],
                         "appellation": r.app, "source_date": dt}

    found = {norm(a) for a in apps["app"]} & GC_KEYS
    missing = sorted(GC_KEYS - found)
    print(f"grand cru check: {len(found)}/{len(GC_KEYS)} matched; missing: {missing}")

    cols = ["id", "name", "country", "level", "rank", "parent", "src"]
    write_features(os.path.join(BUILD, "fr_appellations.geojsonl"), apps, cols)
    write_features(os.path.join(BUILD, "fr_denominations.geojsonl"), dens, cols)
    write_details(os.path.join(BUILD, "fr_details.json"), details)
    print(dens["level"].value_counts().to_dict(), dens["rank"].value_counts().to_dict())


if __name__ == "__main__":
    main()
